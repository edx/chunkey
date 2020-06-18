import os
import sys
import unittest
import subprocess
"""
tests for VidChunk

"""
from chunkey.encode_pipeline import VideoPipeline


@unittest.skip("FFmpeg test")
class TestEncodePipeline(unittest.TestCase):

    def test_command_gen(self):
        """
        Generate an ffmpeg command

        """
        self.Pipeline = VideoPipeline(
            mezz_file=os.path.join(
                os.path.dirname(__file__),
                'OVTESTFILE_01.mp4'
            )
        )
        self.Pipeline._generate_encode()
        self.assertEqual(
            len(self.Pipeline.settings.TRANSCODE_PROFILES),
            len(self.Pipeline.encode_list)
        )
        return self


@unittest.skip("FFmpeg compiled")
class TestFFMPEGCompile(unittest.TestCase):
    def test_ffmpeg_compile(self):
        """
        test if ffmpeg has compiled properly

        """
        process = subprocess.Popen(
            'ffprobe',
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            universal_newlines=True
        )

        probe_commands = []
        for line in iter(process.stdout.readline, b''):
            probe_commands.append(line.strip())

        self.assertTrue(
            "usage: ffprobe [OPTIONS] [INPUT_FILE]" in
            probe_commands
        )


def main():
    unittest.main()


if __name__ == '__main__':
    sys.exit(main())
