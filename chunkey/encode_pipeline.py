"""
Encode streams of input -> output for HLS five stream video

NOTE: Just a test, so will need greater looking into

Generate master manifest, upload (easy, via boto) to output bucket

"""

from __future__ import absolute_import
from __future__ import print_function
import os
import sys
import subprocess
import fnmatch
import shutil
import boto
import boto.s3
from boto.s3.key import Key
import requests

import six
from . import util_functions

try:
    boto.config.add_section('Boto')
except:  # noqa  # pylint: disable=bare-except
    pass
boto.config.set('Boto', 'http_socket_timeout', '600')


class VideoFile(object):
    """
    A simple object for a video file
    """
    def __init__(self, **kwargs):
        self.filepath = kwargs.get('filepath', None)
        self.duration = None
        self.bitrate = None
        self.resolution = None


class TransportStream(object):
    """
    A mini class for the TS
    """
    def __init__(self):
        self.bandwidth = None
        self.resolution = None
        self.ts_manifest = None


class VideoPipeline(object):
    """
    Encode Pipeline
    """
    def __init__(self, mezz_file, **kwargs):
        self.settings = kwargs.get('settings', None)
        self.clean = kwargs.get('clean', True)
        self.mezz_file = mezz_file
        self.encode_list = []
        self.video_id = kwargs.get('video_id', os.path.splitext(os.path.basename(self.mezz_file))[0])
        self.video_root = os.path.join(self.settings.workdir, self.video_id)
        self.manifest = kwargs.get('manifest', self.video_id + '.m3u8')
        self.manifest_data = []
        self.manifest_url = None
        self.file_delivered = False

    def run(self):
        """
        Groom environ, make dirs, clean environ
        """
        if not os.path.exists(self.settings.workdir):
            os.mkdir(self.settings.workdir)

        if not os.path.exists(self.video_root):
            os.mkdir(self.video_root)

        if 'http' in self.mezz_file or 'https' in self.mezz_file:
            if self._download_from_url() is False:
                return False

        self._generate_encode()
        self._execute_encode()
        self._manifest_data()
        self._manifest_generate()
        self.file_delivered = self._upload_transport()
        self._clean_workspace()
        return True

    def _download_from_url(self):
        """
        Function to test and DL from url
        """
        d = requests.head(self.mezz_file, timeout=20)
        print(d.status_code)
        if d.status_code > 299:
            return False

        r = requests.get(self.mezz_file, stream=True)

        with open(os.path.join(
            self.settings.workdir,
            os.path.basename(self.mezz_file)
        ), 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)

        self.mezz_file = os.path.join(
            self.settings.workdir,
            os.path.basename(self.mezz_file)
        )
        return True

    def _scalar_commands(self, profile):
        """
        Padding (if requested and needed)
        letter/pillarboxing Command example: -vf pad=720:480:0:38
        (target reso, x, y)
        """
        scalar_command = "-vf scale=" + profile['scale']
        video_file = VideoFile()
        video_file.filepath = self.mezz_file
        util_functions.probe_video(VideoFileObject=video_file)

        horiz_resolution = float(video_file.resolution.split('x')[0])
        vert_resolution = float(video_file.resolution.split('x')[1])

        # Aspect Ratio as float
        if vert_resolution is not None and horiz_resolution is not None:
            aspect_ratio = float(horiz_resolution) / float(vert_resolution)
        else:
            return scalar_command

        if (aspect_ratio - .00001) <= \
            self.settings.TARGET_ASPECT_RATIO <= \
                (aspect_ratio + .00001):
            return scalar_command

        elif vert_resolution == 1080.0 and horiz_resolution == 1440.0:
            return scalar_command

        # Pad videos with differing aspect ratios, either in pillar or letter box
        target_vertical_resolution = profile['scale'].split(':')[1]
        target_horiz_resolution = profile['scale'].split(':')[0]

        if aspect_ratio > self.settings.TARGET_ASPECT_RATIO:
            # LETTERBOX
            scalar = (float(target_vertical_resolution)
                      - (float(target_horiz_resolution) / aspect_ratio)) / 2

            scalar_command = "-vf scale=" + target_horiz_resolution
            scalar_command += ":" + str(int(target_vertical_resolution)
                                        - (int(scalar) * 2))

            # padding
            scalar_command += ",pad=" + target_horiz_resolution + \
                ":" + target_vertical_resolution
            scalar_command += ":0:" + str(int(scalar))
            return scalar_command
        if aspect_ratio < self.settings.TARGET_ASPECT_RATIO:
            # PILLARBOX
            scalar = (float(target_horiz_resolution)
                      - (aspect_ratio * float(target_vertical_resolution))) / 2

            scalar_command = "-vf scale=" + str(int(target_horiz_resolution)
                                                - (int(scalar) * 2))
            scalar_command += ":" + target_vertical_resolution

            # Padding
            scalar_command += ",pad="
            scalar_command += target_horiz_resolution + ":"
            scalar_command += target_vertical_resolution

            scalar_command += ":" + str(int(scalar)) + ":0 "
            return scalar_command

    def _generate_encode(self):
        """
        Generate ffmpeg commands into array by use in transcode function
        """
        '''
        # ffmpeg -y -i
        /Users/tiagorodriguez/Desktop/HLS_testbed/TEST_VIDEO/HARSPU27T313-V043500_DTH.mp4
        -c:a aac -strict experimental -ac 2 -b:a 96k -ar 44100
        -c:v libx264 -pix_fmt yuv420p -profile:v main
        -level 3.2 -maxrate 2M -bufsize 6M
        -crf 18 -r 24 -g 72 -f hls -hls_time 9 -hls_list_size 0 -s 1280x720
        /Users/tiagorodriguez/Desktop/HLS_testbed/OUTPUT_TEST/1280x720.m3u8

        '''  # pylint: disable=pointless-string-statement
        encode_profiles = self.settings.TRANSCODE_PROFILES
        for profile_name, profile in six.iteritems(encode_profiles):
            ffcommand = ['ffmpeg -y -i']
            ffcommand.append(self.mezz_file)

            # Add Audio
            ffcommand.append("-b:a")
            ffcommand.append(profile['audio_depth'])

            # Add codec
            ffcommand.append("-pix_fmt yuv420p")
            ffcommand.append("-profile:v main -level 3.2")
            ffcommand.append("-maxrate 2M -bufsize 6M")
            ffcommand.append("-c:v")
            ffcommand.append("libx264")
            # Add scaling / rate factor / framerate
            # SCALING COMMANDS
            scalar = self._scalar_commands(profile=profile)
            ffcommand.append(scalar)

            # RATE FACTOR
            ffcommand.append("-crf")
            ffcommand.append(profile['rate_factor'])
            ffcommand.append("-r")
            ffcommand.append(profile['fps'])
            ffcommand.append("-g")
            ffcommand.append("72")
            ffcommand.append("-f")

            # Add HLS Commands
            ffcommand.append("hls")
            ffcommand.append("-hls_time")
            ffcommand.append(str(self.settings.HLS_TIME))
            ffcommand.append("-hls_list_size")
            ffcommand.append("0")
            ffcommand.append("-s")
            ffcommand.append(profile['scale'].replace(':', 'x'))

            # Add output files
            destination = os.path.join(self.video_root, self.video_id)
            destination += '_' + profile_name + '_'
            destination += ".m3u8"

            ffcommand.append(destination)
            if ffcommand:

                self.encode_list.append(' '.join((ffcommand)))
        return None

    def _execute_encode(self):
        # pylint: disable=missing-docstring
        for command in self.encode_list:

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=True,
                universal_newlines=True
            )

            # get vid info, gen status
            util_functions.status_bar(process=process)
            """
            We'll let this fail quietly
            Fault tolerance in manifest gen will pick up.
            """  # pylint: disable=pointless-string-statement
        return None

    def _determine_bandwidth(self, profile_name):
        """
        TODO: Determine more accurate transmission overhead
        """
        max_bandwidth = 0.0

        for input_file in os.listdir(self.video_root):
            if fnmatch.fnmatch(input_file, '*.ts') and \
                    fnmatch.fnmatch(input_file, '_'.join((self.video_id, profile_name, '*'))):
                bandwidth = float(os.stat(os.path.join(self.video_root, input_file)).st_size) / 9
                if bandwidth > max_bandwidth:
                    max_bandwidth = bandwidth

        return max_bandwidth

    def _manifest_data(self):
        '''
        MANIFEST :
        NOTE -- this doesn't seem to work with directories in S3

        #EXTM3U
        #EXT-X-STREAM-INF:BANDWIDTH=192000,RESOLUTION=320x180
        OUTPUT_TEST/XXXXXXXX2015-V000700_.m3u8
        #EXT-X-STREAM-INF:BANDWIDTH=500000,RESOLUTION=480x270
        OUTPUT_TEST/XXXXXXXX2015-V000700_.m3u8
        #EXT-X-STREAM-INF:BANDWIDTH=1000000,RESOLUTION=640x360
        OUTPUT_TEST/XXXXXXXX2015-V000700_.m3u8
        #EXT-X-STREAM-INF:BANDWIDTH=2000000,RESOLUTION=1280x720
        OUTPUT_TEST/XXXXXXXX2015-V000700_.m3u8

        '''
        encode_profiles = self.settings.TRANSCODE_PROFILES

        for profile_name, _ in six.iteritems(encode_profiles):
            T1 = TransportStream()

            # TS manifest
            T1.ts_manifest = self.video_id
            T1.ts_manifest += '_' + profile_name + '_'
            T1.ts_manifest += ".m3u8"

            # Bandwidth
            T1.bandwidth = int(self._determine_bandwidth(
                profile_name=profile_name
            ))

            # resolution
            pre_reso = self.settings.TRANSCODE_PROFILES[profile_name]['scale']
            T1.resolution = pre_reso.replace(':', 'x')

            self.manifest_data.append(T1)

        return None

    def _manifest_generate(self):
        """
        Fault Tolerate corrupt Transport Stream components
        """
        for input_file in os.listdir(self.video_root):
            if fnmatch.fnmatch(input_file, '*.ts'):
                TransportVideoObject = VideoFile(
                    filepath=os.path.join(self.video_root, input_file)
                )
                analyzedTransportVideoObject = util_functions.probe_video(VideoFileObject=TransportVideoObject)
                if analyzedTransportVideoObject.duration is None:
                    """
                    The Transport stream will fail down or up if a ts file is missing, but we cannot remove the
                    ts from the manifest, as the time will "jump" -- HLS will fail-over to the next lower encode
                    for that ~11 sec or empty file
                    """  # pylint: disable=pointless-string-statement
                    os.remove(os.path.join(self.video_root, input_file))

        with open(os.path.join(self.video_root, self.manifest), 'w') as m1:
            m1.write('#EXTM3U')
            m1.write('\n')
            for m in self.manifest_data:
                m1.write('#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=')
                m1.write(str(m.bandwidth))
                m1.write(',')
                m1.write('RESOLUTION=')
                m1.write(m.resolution)
                m1.write('\n')
                m1.write(m.ts_manifest)
                m1.write('\n')

        return None

    def _upload_transport(self):
        """
        **NOTE**
        We won't bother with multipart upload operations here,
        as this should NEVER be that big. We're uploading
        ${settings.HLS_TIME} (default=9) seconds of a squashed file,
        so if you're above 5gB, you're from the future, and you
        should be doing something else or outside playing with your jetpack
        above the sunken city of Miami.

        Upload single part
        """
        if self.settings.ACCESS_KEY_ID is not None:
            conn = boto.connect_s3(
                self.settings.ACCESS_KEY_ID,
                self.settings.SECRET_ACCESS_KEY
            )
        else:
            conn = boto.connect_s3()

        delv_bucket = conn.get_bucket(self.settings.DELIVER_BUCKET)

        for transport_stream in os.listdir(self.video_root):
            if not fnmatch.fnmatch(transport_stream, ".*"):
                upload_key = Key(delv_bucket)
                if self.settings.DELIVER_ROOT is not None:
                    upload_key.key = '/'.join((
                        self.settings.DELIVER_ROOT,
                        self.video_id,
                        transport_stream
                    ))
                else:
                    upload_key.key = '/'.join((
                        self.video_id,
                        transport_stream
                    ))
                    # Actually upload the thing
                sys.stdout.write('\r')
                sys.stdout.write("%s : %s" % ('Upload', transport_stream))  # pylint: disable=unicode-format-string
                upload_key.set_contents_from_filename(
                    os.path.join(self.video_root, transport_stream)
                )
                upload_key.set_acl('public-read')
                sys.stdout.flush()

        if self.settings.DELIVER_ROOT:
            self.manifest_url = '/'.join((
                'https://s3.amazonaws.com',
                self.settings.DELIVER_BUCKET,
                self.settings.DELIVER_ROOT,
                self.video_id,
                self.manifest
            ))

        else:
            self.manifest_url = '/'.join((
                'https://s3.amazonaws.com',
                self.settings.DELIVER_BUCKET,
                self.video_id,
                self.manifest
            ))

        return True

    def _clean_workspace(self):
        """
        Clean out environment
        """
        shutil.rmtree(self.video_root)
        if self.clean is True:
            os.remove(self.mezz_file)


def main():
    pass


if __name__ == '__main__':
    sys.exit(main())
