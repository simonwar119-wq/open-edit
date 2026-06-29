"""MockProvider — 离线、零成本、确定性的"生成"。

没有 FAL_KEY 也能把整条 spine（生成→风格化剪辑→调色→渲染）跑通。
用 FFmpeg 合成一个带标签的测试 clip（testsrc2 有丰富色彩 → 看得出调色生效），
颜色/音调由 prompt 哈希决定（确定性，无需随机数）。
接上真 FAL_KEY 后，FalProvider 直接替换它，EDL 契约不变。
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

from .base import GenerationProvider, GenSpec, GenResult

# macOS 常见字体，drawtext 需要字体文件
_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/SFNS.ttf",
    "/Library/Fonts/Arial.ttf",
]


def _font() -> str | None:
    for f in _FONT_CANDIDATES:
        if Path(f).exists():
            return f
    return None


def _hash_int(s: str) -> int:
    return int(hashlib.sha1(s.encode("utf-8")).hexdigest(), 16)


def _esc(text: str) -> str:
    """drawtext 文本转义。"""
    return (text.replace("\\", "\\\\").replace(":", "\\:")
            .replace("'", "").replace("%", "\\%").replace(",", " "))


class MockProvider(GenerationProvider):
    name = "mock"

    def __init__(self, out_dir: Path | None = None):
        from .. import WORK_DIR
        self.out_dir = out_dir or (WORK_DIR / "gen")
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def estimate_cost(self, spec: GenSpec) -> float:
        return 0.0

    def submit(self, spec: GenSpec) -> GenResult:
        h = _hash_int(spec.prompt + spec.model)
        freq = 180 + (h % 12) * 20            # 220~440Hz 音调，确定性
        tag = f"MOCK ▸ {spec.model}"
        label = _esc((tag + "  |  " + spec.prompt)[:60])
        key = hashlib.sha1((spec.prompt + spec.model + str(spec.duration_s)).encode()).hexdigest()[:12]
        out = self.out_dir / f"gen_{key}.mp4"

        if out.exists():  # 确定性缓存：同 prompt 不重复生成
            return self._result(out, spec)

        vf = (f"testsrc2=size={spec.width}x{spec.height}:rate={spec.fps}:duration={spec.duration_s}")
        font = _font()
        draw = ""
        if font:
            draw = (f",drawtext=fontfile='{font}':text='{label}':fontcolor=white:fontsize=34"
                    f":box=1:boxcolor=black@0.45:boxborderw=12:x=(w-text_w)/2:y=h-180")

        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", vf,
            "-f", "lavfi", "-i", f"sine=frequency={freq}:duration={spec.duration_s}:sample_rate=48000",
            "-filter_complex", f"[0:v]format=yuv420p{draw}[v]",
            "-map", "[v]", "-map", "1:a",
            "-r", str(spec.fps), "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-ar", "48000", "-ac", "2", "-shortest",
            str(out),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            # drawtext/字体问题时降级为纯色块，保证 spine 不断
            cmd_fallback = [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "lavfi", "-i", vf,
                "-f", "lavfi", "-i", f"sine=frequency={freq}:duration={spec.duration_s}:sample_rate=48000",
                "-vf", "format=yuv420p", "-r", str(spec.fps),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-ar", "48000", "-ac", "2", "-shortest", str(out),
            ]
            proc2 = subprocess.run(cmd_fallback, capture_output=True, text=True)
            if proc2.returncode != 0:
                raise RuntimeError(f"MockProvider 生成失败:\n{proc.stderr}\n{proc2.stderr}")
        return self._result(out, spec)

    def _result(self, out: Path, spec: GenSpec) -> GenResult:
        return GenResult(
            local_path=str(out),
            provider=self.name,
            model=spec.model,
            model_version="mock-0",
            cost_usd=0.0,
            commercial_ok=True,
            duration_s=spec.duration_s,
            raw={"prompt": spec.prompt, "kind": spec.kind},
        )
