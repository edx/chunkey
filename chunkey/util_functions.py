"""
"Dumb" utility executables

"""

import sys
import subprocess


def seconds_from_string(duration):
    """
    Return a float (seconds) from something like 00:15:32.33
    """
    hours = float(duration.split(':')[0])
    minutes = float(duration.split(':')[1])
    seconds = float(duration.split(':')[2])
    duration_seconds = (((hours * 60) + minutes) * 60) + seconds
    return duration_seconds


def status_bar(process):
    """
    This is a little gross, but it'll get us a status bar
    """
    fps = None
    duration = None
    while True:
        line = process.stdout.readline().strip()

        if line == '' and process.poll() is not None:
            break
        if fps is None or duration is None:
            if "Stream #" in line and " Video: " in line:
                fps = [s for s in line.split(',') if "fps" in s][0].strip(' fps')

            if "Duration: " in line:
                dur = line.split('Duration: ')[1].split(',')[0].strip()
                duration = seconds_from_string(duration=dur)

        else:
            if 'frame=' in line:
                cur_frame = line.split('frame=')[1].split('fps=')[0].strip()
                end_frame = float(duration) * float(fps.strip())
                pctg = (float(cur_frame) / float(end_frame))

                sys.stdout.write('\r')
                i = int(pctg * 20.0)
                sys.stdout.write("%s : [%-20s] %d%%" % ('Transcode', '=' * i, int(pctg * 100)))
                sys.stdout.flush()

    # For display politeness
    sys.stdout.write('\r')
    sys.stdout.write("%s : [%-20s] %d%%" % ('Transcode', '=' * 20, 100))
    sys.stdout.flush()
    print ''


def probe_video(VideoFileObject):
    """
    Use ffprobe to determine video metadata
    """
    ffprobe_comm = 'ffprobe -hide_banner ' + VideoFileObject.filepath

    p = subprocess.Popen(
        ffprobe_comm,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True
    )

    for line in iter(p.stdout.readline, b''):
        if "Duration: " in line:
            # Duration
            vid_duration = line.split('Duration: ')[1].split(',')[0].strip()
            VideoFileObject.duration = seconds_from_string(
                duration=vid_duration
            )
            # Bitrate
            try:
                VideoFileObject.bitrate = float(line.split('bitrate: ')[1].strip().split()[0])
            except ValueError:
                pass

        elif "Stream #" in line and 'Video: ' in line:
            codec_array = line.strip().split(',')
            for c in codec_array:
                # Resolution
                if len(c.split('x')) == 2:
                    if '[' not in c:
                        VideoFileObject.resolution = c.strip()
                    else:
                        VideoFileObject.resolution = c.strip().split(' ')[0]
    return VideoFileObject
