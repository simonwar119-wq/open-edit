"""风格 profile(v2 JSON) 加载与访问。

profile = 这次的核心 IP：同一份数据同时驱动「剪辑节奏+转场」「CDL/LUT 调色」
「反向分镜（模式B）」「生成镜头的 prompt 风格」。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import PROFILES_DIR, ENGINE_DIR

_ASPECT = {"9:16": (720, 1280), "16:9": (1280, 720), "1:1": (1080, 1080), "4:5": (864, 1080)}


class StyleProfile:
    def __init__(self, data: dict, path: Path):
        self.data = data
        self.path = path

    # ── 加载 ──────────────────────────────────────────────
    @classmethod
    def load(cls, name_or_path: str) -> "StyleProfile":
        p = Path(name_or_path)
        if p.exists() and p.suffix == ".json":
            path = p
        else:
            stem = p.stem if p.suffix == ".json" else name_or_path
            path = PROFILES_DIR / f"{stem}.json"
            if not path.exists():
                raise FileNotFoundError(
                    f"找不到风格 profile: {name_or_path}\n"
                    f"  可用: {[f.stem for f in PROFILES_DIR.glob('*.json')]}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(data, path)

    # ── 访问器 ────────────────────────────────────────────
    @property
    def id(self) -> str:
        return self.data.get("id", self.path.stem)

    @property
    def display_name(self) -> str:
        return self.data.get("display_name", self.id)

    def get(self, *keys, default=None) -> Any:
        node = self.data
        for k in keys:
            if not isinstance(node, dict) or k not in node:
                return default
            node = node[k]
        return node

    @property
    def render_dims(self) -> tuple[int, int]:
        ar = self.get("render", "aspect_ratio", default="9:16")
        return _ASPECT.get(ar, (720, 1280))

    @property
    def fps(self) -> int:
        return int(self.get("render", "fps", default=24))

    @property
    def asl(self) -> float:
        return float(self.get("pacing", "asl_seconds", default=4.0))

    @property
    def shot_len_range(self) -> tuple[float, float]:
        rng = self.get("pacing", "shot_len_p10_p90_s", default=[1.5, 9.0])
        return float(rng[0]), float(rng[1])

    @property
    def lut_abs_path(self) -> Path | None:
        ref = self.get("color", "creative_lut", "ref")
        if not ref:
            return None
        return (ENGINE_DIR / ref).resolve()

    @property
    def shot_prompt_style(self) -> str:
        return self.get("generation_hints", "shot_prompts_style", default="")

    @property
    def preferred_model(self) -> str:
        return self.get("generation_hints", "preferred_video_model", default="seedance-2.0-fast")
