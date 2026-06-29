#!/usr/bin/env python3
"""music — 自动配乐（复用 AutoClip 已策展的 Pixabay 免版权曲库）。

真相：Pixabay/Pexels 都没有音乐 API。AutoClip 的做法（也是对的做法）是人工从
Pixabay 选曲 → 下载 loudnorm → 传自有 OSS → 按 4 类 pick。这里直接复用那批 OSS 曲，
按 director 给的 mood 类别选一首 → 循环/裁到成片长度 → 垫在人声下面(ducking) → 混音。

类别：tech(高级/冷调) | warm(生活/温暖) | energetic(动感/快剪) | cinematic(电影/叙事)
"""

from __future__ import annotations

import argparse
import random
import subprocess
import sys
from pathlib import Path

from . import WORK_DIR

_OSS = "https://autoclip-1.oss-ap-southeast-1.aliyuncs.com/bgm"
_CUR = f"{_OSS}/curated"
_FOOD = f"{_OSS}/food"

# 复用 AutoClip bgm-pool.ts 的策展曲（Pixabay 免版权，attribution 保留以备署名）
BGM_POOL: list[dict] = [
    # tech
    {"id": "tech-01", "cat": "tech", "url": f"{_CUR}/tech-01.wav", "by": "Techno House 2 — monume (Pixabay)"},
    {"id": "tech-02", "cat": "tech", "url": f"{_CUR}/tech-02.wav", "by": "Cyberpunk Sci-Fi Trailer — vasilyatsevich (Pixabay)"},
    {"id": "tech-03", "cat": "tech", "url": f"{_CUR}/tech-03.wav", "by": "Infographics — the_mountain (Pixabay)"},
    # warm
    {"id": "warm-01", "cat": "warm", "url": f"{_FOOD}/food-warm-01.mp3", "by": "Ambient Warm 82bpm"},
    {"id": "warm-02", "cat": "warm", "url": f"{_FOOD}/food-warm-02.mp3", "by": "Ambient Cafe 90bpm"},
    {"id": "warm-04", "cat": "warm", "url": f"{_FOOD}/food-warm-04.mp3", "by": "Story Craft 96bpm"},
    # energetic
    {"id": "energy-01", "cat": "energetic", "url": f"{_CUR}/energy-01.wav", "by": "Motivational Fire — joyinsound (Pixabay)"},
    {"id": "energy-02", "cat": "energetic", "url": f"{_CUR}/energy-02.wav", "by": "No Copyright Music — joyinsound (Pixabay)"},
    {"id": "food-energy-01", "cat": "energetic", "url": f"{_FOOD}/food-energy-01.mp3", "by": "Beat Fire 120bpm"},
    # cinematic
    {"id": "cinema-01", "cat": "cinematic", "url": f"{_CUR}/cinema-01.wav", "by": "Adventure Trailer — jonasblakewood (Pixabay)"},
    {"id": "cinema-02", "cat": "cinematic", "url": f"{_CUR}/cinema-02.wav", "by": "Adventure Trailer 60s — jonasblakewood (Pixabay)"},
    {"id": "cinema-03", "cat": "cinematic", "url": f"{_CUR}/cinema-03.wav", "by": "Background Music — eliveta (Pixabay)"},
    {"id": "food-cinema-01", "cat": "cinematic", "url": f"{_FOOD}/food-cinema-01.mp3", "by": "Premium Steak 84bpm"},
]

CATEGORIES = ("tech", "warm", "energetic", "cinematic")

# style → 默认音乐类别（director 没给类别时兜底）
STYLE_TO_CATEGORY = {
    "fincher-inspired": "cinematic",
    "wes-anderson-inspired": "warm",
}


def normalize_category(hint: str | None) -> str:
    v = (hint or "").lower().strip()
    if v in CATEGORIES:
        return v
    table = {"epic": "cinematic", "dramatic": "cinematic", "emotional": "cinematic", "calm": "cinematic",
             "modern": "tech", "minimal": "tech", "cool": "tech", "clean": "tech",
             "cozy": "warm", "elegant": "warm", "soft": "warm",
             "upbeat": "energetic", "lively": "energetic", "fast": "energetic", "happy": "energetic"}
    for k, c in table.items():
        if k in v:
            return c
    return "cinematic"


def pick_bgm(category: str | None) -> dict | None:
    cat = normalize_category(category)
    pool = [t for t in BGM_POOL if t["cat"] == cat] or BGM_POOL
    return random.choice(pool) if pool else None


def _download(track: dict) -> Path:
    cache = WORK_DIR / "music"
    cache.mkdir(parents=True, exist_ok=True)
    ext = ".wav" if track["url"].endswith(".wav") else ".mp3"
    out = cache / f"{track['id']}{ext}"
    if not out.exists() or out.stat().st_size == 0:
        # 用 curl（本环境有 HTTP 代理，urllib 会拿到 0 字节）
        subprocess.run(["curl", "-sL", "-A", "Mozilla/5.0", track["url"], "-o", str(out)],
                       check=True)
    return out


def add_music(video: str, out: str, category: str | None = None,
              bed_volume: float = 0.22, log=lambda m: None) -> dict:
    """给成片加背景乐：循环到片长 + 人声下垫底(ducking) + 混音。"""
    track = pick_bgm(category)
    if not track:
        log("无可用曲库，跳过配乐")
        return {"skipped": True, "out": video}
    log(f"配乐[{normalize_category(category)}] {track['id']} — {track['by']}")
    music = _download(track)

    # [1:a] 循环的音乐压到 bed_volume 垫底；与人声 amix，按视频时长收尾(duration=first)
    fc = (f"[1:a]volume={bed_volume},aresample=48000[bg];"
          f"[0:a][bg]amix=inputs=2:duration=first:normalize=0[a]")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", video, "-stream_loop", "-1", "-i", str(music),
                    "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-ar", "48000", "-ac", "2",
                    "-shortest", str(out)], check=True)
    log(f"配乐成片 → {Path(out).name}")
    return {"skipped": False, "out": out, "track": track["id"], "attribution": track["by"],
            "category": normalize_category(category)}


def main():
    ap = argparse.ArgumentParser(description="Open Edit — music (自动配乐)")
    ap.add_argument("video")
    ap.add_argument("--out", default=str(WORK_DIR / "with_music.mp4"))
    ap.add_argument("--category", default=None, choices=[None, *CATEGORIES])
    args = ap.parse_args()
    r = add_music(args.video, args.out, args.category,
                  log=lambda m: print("  " + m, file=sys.stderr))
    print(args.out if not r["skipped"] else args.video)


if __name__ == "__main__":
    main()
