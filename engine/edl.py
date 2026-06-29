"""EDL(Edit Decision List) — 整条流水线的合同。

Claude/build_edl 只产出 EDL(JSON)；纯函数 render.py 消费它 → 渲染可复现、可 diff、可重跑、
可被用户在 NLE 里精修。这是区别于"LLM 直接出片"的关键设计。

EDL 结构（JSON）：
{
  "version": "1.0",
  "style_id": "fincher-inspired-v1",
  "prompt": "...",
  "render": {"width":720,"height":1280,"fps":24,"codec":"h264"},
  "color":  { ...profile.color 原样... },
  "audio":  {"normalize_lufs":-14},
  "clips": [
     {"id":"c1","source":"/abs.mp4","in":0.0,"out":3.5,"origin":"generated|upload",
      "role":"hook","transition_in":{"type":"cut","duration":0.0},
      "gen":{"provider":"mock","model":"...","cost_usd":0.0,"commercial_ok":true,"prompt":"..."}}
  ],
  "cost": {"reserve_usd": 0.0, "spent_usd": 0.0}
}
"""

from __future__ import annotations

import json
from pathlib import Path

EDL_VERSION = "1.0"


def new_edl(style_id: str, prompt: str, width: int, height: int, fps: int,
            color: dict, audio: dict) -> dict:
    return {
        "version": EDL_VERSION,
        "style_id": style_id,
        "prompt": prompt,
        "render": {"width": width, "height": height, "fps": fps, "codec": "h264"},
        "color": color or {},
        "audio": audio or {},
        "clips": [],
        "cost": {"reserve_usd": 0.0, "spent_usd": 0.0},
    }


def validate(edl: dict) -> list[str]:
    """返回问题列表（空 = 通过）。render 前先校验，保证纯函数可消费。"""
    errs: list[str] = []
    if edl.get("version") != EDL_VERSION:
        errs.append(f"version 必须是 {EDL_VERSION}")
    r = edl.get("render", {})
    for k in ("width", "height", "fps"):
        if not isinstance(r.get(k), int) or r[k] <= 0:
            errs.append(f"render.{k} 非法")
    clips = edl.get("clips", [])
    if not clips:
        errs.append("clips 为空")
    for i, c in enumerate(clips):
        src = c.get("source")
        if not src or not Path(src).exists():
            errs.append(f"clip[{i}] source 不存在: {src}")
        if not (c.get("out", 0) > c.get("in", 0)):
            errs.append(f"clip[{i}] in/out 非法: in={c.get('in')} out={c.get('out')}")
        t = c.get("transition_in", {})
        if i == 0 and t.get("type") not in (None, "cut"):
            errs.append("clip[0] 不应有非 cut 的入转场")
    return errs


def save(edl: dict, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(edl, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def clip_duration(c: dict) -> float:
    return round(float(c["out"]) - float(c["in"]), 4)
