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
import math
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
    has_j_cut = any((c.get("transition_in") or {}).get("type") == "j-cut" for c in clips)
    if not clips:
        errs.append("clips 为空")
    for i, c in enumerate(clips):
        src = c.get("source")
        if not src or not Path(src).exists():
            errs.append(f"clip[{i}] source 不存在: {src}")
        start, end = c.get("in", 0), c.get("out", 0)
        valid_times = all(isinstance(x, (int, float)) and not isinstance(x, bool)
                          and math.isfinite(x) for x in (start, end))
        if not valid_times or not (end > start >= 0):
            errs.append(f"clip[{i}] in/out 非法: in={c.get('in')} out={c.get('out')}")
            continue
        t = c.get("transition_in") or {}
        if i == 0 and t.get("type") not in (None, "cut"):
            errs.append("clip[0] 不应有非 cut 的入转场")
        if has_j_cut and t.get("type") not in (None, "cut", "dissolve", "j-cut"):
            errs.append(f"clip[{i}] 不支持的转场: {t.get('type')}")
        if has_j_cut and t.get("type") == "dissolve":
            overlap = t.get("duration")
            if (not isinstance(overlap, (int, float)) or isinstance(overlap, bool)
                    or not math.isfinite(overlap) or overlap <= 0 or overlap >= end - start):
                errs.append(f"clip[{i}] dissolve duration 非法")
                continue
            if i:
                try:
                    if overlap >= clip_duration(clips[i - 1]):
                        errs.append(f"clip[{i}] dissolve duration 超出前镜头")
                except (TypeError, ValueError, KeyError):
                    errs.append(f"clip[{i}] 前镜头时长非法")
        if t.get("type") == "j-cut":
            lead = t.get("duration")
            if not isinstance(lead, (int, float)) or isinstance(lead, bool) or not math.isfinite(lead) or lead <= 0:
                errs.append(f"clip[{i}] J-cut duration 必须是有限正秒数")
                continue
            if start + 1e-6 < lead:
                errs.append(f"clip[{i}] J-cut 源音频余量不足: in 必须 >= duration")
            if i:
                previous = clips[i - 1]
                try:
                    available = clip_duration(previous)
                    pt = previous.get("transition_in") or {}
                    if pt.get("type") == "dissolve":
                        available -= float(pt.get("duration", 0))
                    if lead >= available:
                        errs.append(f"clip[{i}] J-cut duration 必须小于前镜头可用时长")
                except (TypeError, ValueError, KeyError):
                    errs.append(f"clip[{i}] 前镜头时长非法")
        # A J-cut picture boundary must land on an output frame, otherwise
        # rounding the video alone would shift its source time against audio.
        if has_j_cut and isinstance(r.get("fps"), int) and r["fps"] > 0:
            times = [start, end]
            if t.get("type") in ("j-cut", "dissolve"):
                times.append(t["duration"])
            if any(abs(x * r["fps"] - round(x * r["fps"])) > 1e-4 for x in times):
                errs.append(f"clip[{i}] J-cut 时间线的 in/out/duration 必须对齐 {r['fps']}fps 帧边界")
    return errs


def set_j_cuts(edl: dict, specifications: list[str]) -> None:
    """Apply CLI CLIP_ID:SECONDS choices without changing source in/out points."""
    for spec in specifications:
        try:
            clip_id, value = spec.rsplit(":", 1)
            duration = float(value)
        except ValueError as exc:
            raise ValueError("--j-cut 格式为 CLIP_ID:SECONDS，例如 c2:0.5") from exc
        matches = [c for c in edl.get("clips", []) if c.get("id") == clip_id]
        if len(matches) != 1:
            raise ValueError(f"--j-cut 需要唯一 clip id: {clip_id}")
        matches[0]["transition_in"] = {"type": "j-cut", "duration": duration}


def save(edl: dict, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(edl, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def clip_duration(c: dict) -> float:
    return round(float(c["out"]) - float(c["in"]), 4)
