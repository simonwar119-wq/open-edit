"""素材分析 —— 给「AI 导演」喂真实的画面特征（不是瞎猜）。

只用 ffmpeg/ffprobe（零新依赖），快速提取每条素材的：
  分辨率/时长/帧率、平均亮度/饱和度/色相、镜头切换数 → 节奏(shots/秒)。
这些特征 + prompt + 可用风格库 一起喂给 LLM，让它判断「这批素材适合哪个导演风格、缺什么镜头」。
生产可换更强的 Vision（豆包/CLIP 逐镜头打标），接口不变。
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

_ANALYZE_SECONDS = 12  # 只分析前 N 秒，控时


def _probe(path: str) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate",
         "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1", path],
        capture_output=True, text=True).stdout
    d = {}
    for line in out.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            d[k] = v
    w = int(d.get("width", 0) or 0)
    h = int(d.get("height", 0) or 0)
    fr = d.get("r_frame_rate", "0/1")
    try:
        num, den = fr.split("/")
        fps = round(float(num) / float(den), 2) if float(den) else 0.0
    except Exception:
        fps = 0.0
    dur = float(d.get("duration", 0) or 0)
    return {"width": w, "height": h, "fps": fps, "duration_s": round(dur, 2),
            "orientation": "vertical" if h >= w else "horizontal"}


def _signalstats(path: str) -> dict:
    """采样若干帧的亮度/饱和度/色相均值（YAVG 0-255, SATAVG 0-~180, HUEAVG 度）。"""
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-t", str(_ANALYZE_SECONDS), "-i", path,
         "-vf", "select='not(mod(n,20))',signalstats,metadata=mode=print:file=-",
         "-an", "-f", "null", "-"],
        capture_output=True, text=True)
    text = p.stdout + p.stderr
    def avg(key):
        vals = [float(x) for x in re.findall(rf"signalstats\.{key}=([\d.]+)", text)]
        return round(sum(vals) / len(vals), 1) if vals else None
    y, s, hue = avg("YAVG"), avg("SATAVG"), avg("HUEAVG")
    brightness = None if y is None else round(y / 255, 2)
    saturation = None if s is None else round(min(s / 128, 1.0), 2)
    return {"brightness": brightness, "saturation": saturation, "hue_deg": hue,
            "tone": _tone(brightness, saturation)}


def _tone(brightness, saturation) -> str:
    if brightness is None:
        return "unknown"
    if brightness < 0.35:
        return "dark"
    if brightness > 0.65 and (saturation or 0) < 0.4:
        return "high-key"
    if (saturation or 0) > 0.55:
        return "saturated"
    return "neutral"


def _scene_count(path: str) -> int:
    """镜头切换数（select gt(scene,0.3) + showinfo 计数）→ 节奏代理。"""
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-t", str(_ANALYZE_SECONDS), "-i", path,
         "-vf", "select='gt(scene,0.3)',showinfo", "-an", "-f", "null", "-"],
        capture_output=True, text=True)
    return len(re.findall(r"pts_time:", p.stderr))


def analyze_asset(path: str) -> dict:
    if not Path(path).exists():
        return {"path": path, "error": "not found"}
    info = _probe(path)
    info.update(_signalstats(path))
    cuts = _scene_count(path)
    dur = info.get("duration_s") or 1
    info["scene_cuts"] = cuts
    info["cuts_per_min"] = round(cuts / max(min(dur, _ANALYZE_SECONDS), 1) * 60, 1)
    info["pace"] = "fast" if info["cuts_per_min"] > 30 else ("slow" if info["cuts_per_min"] < 8 else "medium")
    info["filename"] = Path(path).name
    info["path"] = str(Path(path).resolve())
    info["already_graded"] = (info.get("saturation") or 0) >= 0.05  # 近纯灰(<0.05)才算 raw/log
    return info


def analyze_assets(paths: list[str]) -> dict:
    assets = [analyze_asset(p) for p in paths]
    valid = [a for a in assets if "error" not in a]
    agg = {}
    if valid:
        def mean(key):
            xs = [a[key] for a in valid if a.get(key) is not None]
            return round(sum(xs) / len(xs), 2) if xs else None
        agg = {"count": len(valid), "total_duration_s": round(sum(a["duration_s"] for a in valid), 1),
               "avg_brightness": mean("brightness"), "avg_saturation": mean("saturation"),
               "avg_cuts_per_min": mean("cuts_per_min"),
               "orientation": valid[0]["orientation"]}
    return {"assets": assets, "aggregate": agg}


if __name__ == "__main__":
    import json, sys
    print(json.dumps(analyze_assets(sys.argv[1:]), ensure_ascii=False, indent=2))
