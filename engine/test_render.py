"""Offline regression checks using bounded FFmpeg subprocesses and decoded media.

Written independently for PR #4/#5 integration; no contributor test code runs.
"""
import array
import copy
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from . import LUTS_DIR
from .edl import new_edl, validate, set_j_cuts
from .render import color_chain, render_edl


def command(args):
    """Run a local media operation with a hard deadline."""
    result = subprocess.run(args, capture_output=True, timeout=45)
    if result.returncode:
        raise AssertionError(result.stderr.decode(errors="replace")[-4000:])
    return result.stdout


def ffmpeg(*args):
    return command(["ffmpeg", "-v", "error", "-y", *map(str, args)])


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "requires FFmpeg/ffprobe")
class LUTPathTests(unittest.TestCase):
    def test_pixels_match_plain_path_at_both_intensities(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plain = root / "look.cube"
            shutil.copyfile(LUTS_DIR / "bleach-bypass.cube", plain)
            # Colon and literal backslash are legal POSIX filenames. On Windows,
            # the temp directory's actual drive letter exercises the colon.
            names = ["Open Edit's [LUT], test; 中文"]
            if os.name != "nt":
                names += ["E: drive \\ and ' comma,;[]"]
            def pixels(path, intensity):
                graph, _ = color_chain({"creative_lut": {"ref": str(path), "intensity": intensity}}, 24, 32, 32)
                return ffmpeg("-f", "lavfi", "-i", "testsrc2=s=32x32:r=24:d=0.125",
                              "-filter_complex", graph, "-map", "[outv]", "-frames:v", "3",
                              "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1")
            baseline = pixels(plain, 0)
            for intensity in (1.0, 0.7):
                expected = pixels(plain, intensity)
                self.assertEqual(len(expected), 32 * 32 * 3 * 3)
                self.assertNotEqual(expected, baseline, "LUT must actually change pixels")
                for name in names:
                    with self.subTest(intensity=intensity, path=name):
                        folder = root / name
                        folder.mkdir(exist_ok=True)
                        special = folder / "look.cube"
                        shutil.copyfile(plain, special)
                        self.assertEqual(pixels(special, intensity), expected)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "requires FFmpeg/ffprobe")
class JCutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="open-edit-jcut-")
        cls.root = Path(cls.temp.name)
        cls.a = cls.root / "a.mp4"
        cls.b = cls.root / "b.mp4"
        cls.silent = cls.root / "silent.mp4"
        ffmpeg("-f", "lavfi", "-i", "color=red:s=64x64:r=24:d=2",
               "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=2",
               "-c:v", "libx264", "-c:a", "aac", cls.a)
        # Source B changes tone exactly at its picture in-point (0.5 s).
        ffmpeg("-f", "lavfi", "-i",
               "color=green:s=64x64:r=24:d=0.5[g];color=blue:s=64x64:r=24:d=1[b];"
               "color=yellow:s=64x64:r=24:d=1[y];[g][b][y]concat=n=3:v=1:a=0",
               "-f", "lavfi", "-i",
               r"aevalsrc=0.2*sin(2*PI*if(lt(t\,0.5)\,880\,if(lt(t\,1.5)\,1320\,1760))*t):s=48000:d=2.5",
               "-c:v", "libx264", "-c:a", "aac", cls.b)
        ffmpeg("-f", "lavfi", "-i", "color=red:s=64x64:r=24:d=2.5",
               "-c:v", "libx264", cls.silent)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def edl(self):
        edl = new_edl("test", "offline", 64, 64, 24, {}, {})
        edl["clips"] = [
            {"id": "c1", "source": str(self.a), "in": 0, "out": 2, "origin": "upload",
             "grade": {"mode": "preserve"}, "transition_in": {"type": "cut", "duration": 0}},
            {"id": "c2", "source": str(self.b), "in": 0.5, "out": 2.5, "origin": "upload",
             "grade": {"mode": "preserve"}, "transition_in": {"type": "j-cut", "duration": 0.5}},
        ]
        return edl

    def render(self, edl, name):
        out = self.root / (name + ".mp4")
        with patch("engine.render.run", side_effect=command):
            render_edl(edl, out, self.root / name)
        return out

    def media_info(self, out):
        # Decode every video/audio frame, not only headers or the exit code.
        ffmpeg("-i", out, "-f", "null", "-")
        info = json.loads(command(["ffprobe", "-v", "error", "-count_frames", "-show_streams",
                                   "-show_format", "-of", "json", str(out)]))
        return info

    def test_audio_enters_early_and_stays_in_sync_at_picture_cut(self):
        out = self.render(self.edl(), "jcut")
        info = self.media_info(out)
        video = next(s for s in info["streams"] if s["codec_type"] == "video")
        self.assertEqual(int(video["nb_read_frames"]), 96)
        self.assertAlmostEqual(float(info["format"]["duration"]), 4, delta=0.025)
        frames = ffmpeg("-i", out, "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1")
        def center(frame):
            offset = frame * 64 * 64 * 3 + (32 * 64 + 32) * 3
            return tuple(frames[offset:offset + 3])
        self.assertGreater(center(47)[0], 220)
        self.assertGreater(center(48)[2], 220)
        self.assertGreater(center(71)[2], 220)
        self.assertGreater(center(72)[0], 220)
        self.assertGreater(center(72)[1], 220)
        self.assertLess(center(72)[2], 30)
        samples = array.array("f", ffmpeg("-i", out, "-vn", "-ac", "1", "-ar", "48000",
                                         "-f", "f32le", "pipe:1"))
        self.assertAlmostEqual(len(samples) / 48000, 4, delta=0.025)
        def tone(start, frequency, length=0.025):
            window = samples[round(start * 48000):round((start + length) * 48000)]
            re = sum(x * math.cos(2 * math.pi * frequency * i / 48000) for i, x in enumerate(window))
            im = sum(x * math.sin(2 * math.pi * frequency * i / 48000) for i, x in enumerate(window))
            return 2 * math.hypot(re, im) / len(window)
        self.assertLess(tone(1.3, 880), 0.005)
        self.assertGreater(tone(1.75, 880), 0.04)
        self.assertGreater(tone(1.75, 440), 0.02)
        self.assertGreater(tone(1.965, 880), 0.12)
        self.assertLess(tone(1.965, 1320), 0.01)
        self.assertGreater(tone(2.025, 1320), 0.12)
        self.assertLess(tone(2.025, 880), 0.01)
        self.assertGreater(tone(2.965, 1320), 0.12)
        self.assertGreater(tone(3.025, 1760), 0.12)
        self.assertLess(tone(3.025, 1320), 0.01)
        if os.environ.get("OPENEDIT_TEST_ARTIFACTS"):
            dest = Path(os.environ["OPENEDIT_TEST_ARTIFACTS"])
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(out, dest / "j-cut-verified.mp4")
            (dest / "j-cut-probe.json").write_text(json.dumps(info, indent=2))

    def test_standalone_recipe_equivalent(self):
        """Independently build the documented two-source recipe, no shell script."""
        graph = []
        for i, start, end in ((0, 0, 2), (1, 0.5, 2.5)):
            graph.append(f"[{i}:v]trim=start={start}:end={end},setpts=PTS-STARTPTS,"
                         "fps=24,scale=1280:720:force_original_aspect_ratio=decrease:force_divisible_by=2,"
                         f"pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p[v{i}]")
            graph.append(f"[{i}:a]atrim=start=0:end={end},asetpts=PTS-STARTPTS,aresample=48000,"
                         f"aformat=sample_fmts=fltp:channel_layouts=stereo[a{i}]")
        graph += ["[v0][v1]concat=n=2:v=1:a=0[v]", "[a0][a1]acrossfade=d=0.5:c1=tri:c2=tri[a]"]
        out = self.root / "recipe.mp4"
        ffmpeg("-i", self.a, "-i", self.b, "-filter_complex", ";".join(graph),
               "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-c:a", "aac",
               "-movflags", "+faststart", out)
        info = self.media_info(out)
        video = next(s for s in info["streams"] if s["codec_type"] == "video")
        self.assertEqual(int(video["nb_read_frames"]), 96)
        self.assertEqual((video["width"], video["height"]), (1280, 720))
        self.assertAlmostEqual(float(info["format"]["duration"]), 4, delta=0.025)

    def test_silent_outgoing_clip(self):
        edl = self.edl()
        edl["clips"][0]["source"] = str(self.silent)
        info = self.media_info(self.render(edl, "silent-a"))
        self.assertEqual(len(info["streams"]), 2)
        self.assertAlmostEqual(float(info["format"]["duration"]), 4, delta=0.025)

    def test_silent_incoming_is_rejected_before_render(self):
        edl = self.edl()
        edl["clips"][1]["source"] = str(self.silent)
        with self.assertRaisesRegex(ValueError, "音轨"):
            self.render(edl, "silent-b")
        self.assertFalse((self.root / "silent-b").exists())

    def test_consecutive_j_cuts(self):
        edl = self.edl()
        edl["clips"].append(dict(edl["clips"][1], id="c3"))
        info = self.media_info(self.render(edl, "consecutive"))
        video = next(s for s in info["streams"] if s["codec_type"] == "video")
        self.assertEqual(int(video["nb_read_frames"]), 144)
        self.assertAlmostEqual(float(info["format"]["duration"]), 6, delta=0.025)

    def test_j_cut_mixed_with_dissolve_and_legacy_cut(self):
        for kind, duration in (("dissolve", 0.5), ("cut", 0)):
            with self.subTest(kind=kind):
                edl = self.edl()
                edl["clips"].append(dict(edl["clips"][0], id="c3",
                                         transition_in={"type": kind, "duration": duration}))
                info = self.media_info(self.render(edl, "mixed-" + kind))
                expected = 5.5 if kind == "dissolve" else 6 - 1 / 24
                self.assertAlmostEqual(float(info["format"]["duration"]), expected, delta=1 / 24)

    def test_j_cut_after_dissolve(self):
        edl = self.edl()
        incoming = copy.deepcopy(edl["clips"][1])
        edl["clips"][1]["transition_in"] = {"type": "dissolve", "duration": 0.5}
        edl["clips"].append(dict(incoming, id="c3"))
        info = self.media_info(self.render(edl, "dissolve-then-j"))
        video = next(s for s in info["streams"] if s["codec_type"] == "video")
        self.assertEqual(int(video["nb_read_frames"]), 132)
        self.assertAlmostEqual(float(info["format"]["duration"]), 5.5, delta=0.025)

    def test_short_outgoing_audio_does_not_shorten_video(self):
        source = self.root / "short-audio.mp4"
        ffmpeg("-f", "lavfi", "-i", "color=red:s=64x64:r=24:d=2",
               "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=1",
               "-c:v", "libx264", "-c:a", "aac", source)
        edl = self.edl()
        edl["clips"][0]["source"] = str(source)
        info = self.media_info(self.render(edl, "short-audio"))
        self.assertAlmostEqual(float(info["format"]["duration"]), 4, delta=0.025)

    def test_long_audio_cannot_hide_missing_video(self):
        source = self.root / "short-video.mp4"
        ffmpeg("-f", "lavfi", "-i", "color=red:s=64x64:r=24:d=1",
               "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=3",
               "-c:v", "libx264", "-c:a", "aac", source)
        edl = self.edl()
        edl["clips"][0]["source"] = str(source)
        with self.assertRaisesRegex(ValueError, "视频不足"):
            self.render(edl, "short-video-result")

    @unittest.skipUnless(importlib.util.find_spec("httpx"), "CLI requires existing httpx dependency")
    def test_actual_cli_renders_selected_j_cut(self):
        edl = self.edl()
        edl["clips"][1]["transition_in"] = {"type": "cut", "duration": 0}
        source = self.root / "cli.edl.json"
        source.write_text(json.dumps(edl))
        before = source.read_bytes()
        out = self.root / "cli.mp4"
        cli = Path(__file__).resolve().parents[1] / "oe.py"
        result = json.loads(command([sys.executable, str(cli), "render", str(source),
                                     "--j-cut", "c2:0.5", "--out", str(out)]))
        self.assertAlmostEqual(result["duration_s"], 4, delta=0.025)
        self.assertEqual(source.read_bytes(), before)
        self.media_info(out)

    def test_legacy_and_single_clip_exports(self):
        for kind, duration in (("cut", 0), ("dissolve", 0.5), ("single", 0)):
            with self.subTest(kind=kind):
                edl = self.edl()
                edl["clips"][1]["transition_in"] = {"type": kind, "duration": duration}
                if kind == "single":
                    edl["clips"] = edl["clips"][:1]
                info = self.media_info(self.render(edl, "legacy-" + kind))
                expected = 2 if kind == "single" else (3.5 if kind == "dissolve" else 4 - 1 / 24)
                self.assertAlmostEqual(float(info["format"]["duration"]), expected, delta=0.06)

    def test_invalid_edits_rejected(self):
        for lead in (0, -0.5, float("nan"), float("inf"), "0.5", True, 2, 0.51):
            with self.subTest(lead=lead):
                edl = self.edl()
                edl["clips"][1]["transition_in"]["duration"] = lead
                self.assertTrue(validate(edl))
        edl = self.edl()
        edl["clips"][1]["in"] = 0
        self.assertTrue(validate(edl))
        edl = self.edl()
        edl["clips"][0]["transition_in"] = {"type": "j-cut", "duration": 0.5}
        self.assertTrue(validate(edl))
        edl = self.edl()
        edl["clips"][1]["out"] = 5
        with self.assertRaisesRegex(ValueError, "素材时长"):
            self.render(edl, "too-long")

    def test_cli_selection_keeps_source_times(self):
        edl = self.edl()
        before = copy.deepcopy(edl["clips"][1])
        set_j_cuts(edl, ["c2:0.25"])
        self.assertEqual(edl["clips"][1]["in"], before["in"])
        self.assertEqual(edl["clips"][1]["out"], before["out"])
        self.assertEqual(edl["clips"][1]["transition_in"]["duration"], 0.25)
        for selection in (["missing:0.5"], ["c2"], ["c2:no"]):
            with self.assertRaises(ValueError):
                set_j_cuts(edl, selection)


if __name__ == "__main__":
    unittest.main()
