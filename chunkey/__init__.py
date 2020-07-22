import os
import sys
import json
import pytest

from .encode_pipeline import VideoPipeline
from . import util_functions


class Chunkey(object):
    """
CHUNKEY

will convert an extant S3 object to an HLS stream (streams determined
by encode_profiles.json) and generate a manifest -- all of which
will be uploaded next to the salient mezzanine file, and delivered to
the "delivery bucket" (with an included tag for "delivery root"
if you're into directories on S3)

example use:
    VideoChunkerInstance = Chunkey(
        mezz_file = path/to/mezz_file, (can be URL)
        DELIVER_BUCKET=AWS S3 bucket to deliver to, [optional]
        ACCESS_KEY_ID=AWS Access key ID, [optional]
        SECRET_ACCESS_KEY=AWS Secret Access Key [optional]
        )
    print VideoChunkerInstance.manifest_url

Copyright (C) 2016 @edx | edX

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
    def __init__(self, **kwargs):
        self.mezz_file = kwargs.get('mezz_file', None)
        self.manifest = kwargs.get('manifest', None)
        self.manifest_url = None
        self.clean = kwargs.get('clean', True)
        self.settings = Globals()
        for key, value in kwargs.items():
            setattr(self.settings, key, value)
        self.Pipeline = None
        if self.mezz_file is not None:
            self.complete = self._run()
        else:
            self.complete = self._test()

    def _run(self):
        """
        Regular run
        """
        self.Pipeline = VideoPipeline(
            settings=self.settings,
            mezz_file=self.mezz_file,
            clean=self.clean
        )

        if self.manifest is not None:
            if '.m3u8' not in self.manifest:
                self.manifest += '.m3u8'

            self.Pipeline.manifest = self.manifest
        self.complete = self.Pipeline.run()
        self.manifest_url = self.Pipeline.manifest_url
        return self.complete

    def _test(self):
        """
        Run tests
        """
        current_dir = os.getcwd()

        test_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'tests'
        )
        os.chdir(test_dir)
        test_bool = pytest.run()

        # Return to previous state
        os.chdir(current_dir)
        return test_bool


class Globals(object):
    """
    global variables
    """
    def __init__(self, **kwargs):
        self.workdir = kwargs.get(
            'work_dir',
            os.path.join(os.getcwd(), 'workdir')
        )
        self.encode_profiles = kwargs.get(
            'encode_profiles',
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'encode_profiles.json'
            )
        )
        with open(self.encode_profiles) as encode_data_file:
            encode_data = json.load(encode_data_file)
        self.TRANSCODE_PROFILES = encode_data['ENCODE_PROFILES']
        self.HLS_TIME = encode_data['HLS_TIME']
        self.TARGET_ASPECT_RATIO = float(16) / float(9)
        self.DELIVER_BUCKET = kwargs.get('DELIVER_BUCKET', None)
        self.DELIVER_ROOT = kwargs.get('DELIVER_ROOT', None)
        self.ACCESS_KEY_ID = kwargs.get('ACCESS_KEY_ID', None)
        self.SECRET_ACCESS_KEY = kwargs.get('SECRET_ACCESS_KEY', None)


def main():
    pass


if __name__ == '__main__':
    sys.exit(main())
