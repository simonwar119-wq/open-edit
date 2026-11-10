import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from . import LUTS_DIR
from .render import color_chain


@unittest.skipUnless(shutil.which("ffmpeg"), "requires FFmpeg")
class ColorChainTests(unittest.TestCase):
    def test_creative_lut_path_with_filtergraph_punctuation(self):
        with tempfile.TemporaryDirectory(prefix="Open Edit's [LUT], test; ") as directory:
            lut = Path(directory) / "look.cube"
            shutil.copyfile(LUTS_DIR / "bleach-bypass.cube", lut)

            for intensity in (1.0, 0.7):
                with self.subTest(intensity=intensity):
                    color = {"creative_lut": {"ref": str(lut), "intensity": intensity}}
                    graph, _ = color_chain(color, 24, 32, 32)
                    result = subprocess.run(
                        [
                            "ffmpeg", "-v", "error", "-f", "lavfi",
                            "-i", "testsrc2=size=32x32:rate=24",
                            "-filter_complex", graph, "-map", "[outv]",
                            "-frames:v", "1", "-pix_fmt", "yuv420p", "-f", "rawvideo", "pipe:1",
                        ],
                        capture_output=True,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
                    self.assertEqual(len(result.stdout), 32 * 32 * 3 // 2)
