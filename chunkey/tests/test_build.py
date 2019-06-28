"""
main build test

Note: until we include ffmpeg in the build, there's only so much we can do

"""
from __future__ import absolute_import
import os
import sys
import unittest
import json

import chunkey.util_functions
from chunkey import VidChunk
import chunkey.encode_pipeline


class TestVidChunkBuild(unittest.TestCase):

    def setUp(self):
        self.encode_profiles = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            'encode_profiles.json'
        )

        with open(self.encode_profiles) as encode_data_file:
            self.encode_data = json.load(encode_data_file)

    def test_encodes(self):
        self.assertTrue(isinstance(self.encode_data, dict))
        self.assertTrue(isinstance(self.encode_data['HLS_TIME'], int))

    def test_utils(self):
        seconds = util_functions.seconds_from_string(duration='00:01:00')
        self.assertTrue(seconds == 60.0)


def main():
    unittest.main()

if __name__ == '__main__':
    sys.exit(main())
