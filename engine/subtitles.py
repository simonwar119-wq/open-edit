#!/usr/bin/env python3
"""subtitles — Whisper 词级转录 → ASS 卡拉OK逐字字幕 → FFmpeg 烧录。

流程（研究结论：对最终成片音轨转录，时间轴最稳）：
  成片 → 抽音轨(16k mono) → faster-whisper 词级时间戳 → 组句 → ASS \\k 卡拉OK → ass 滤镜烧录

Transcriber 可换（faster-whisper 本机 / WhisperX 服务器 CUDA），ASS+烧录无依赖。
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

from . import WORK_DIR

# macOS 中文字体（libass 渲染中文需要，否则豆腐块）
_CJK_FONT_DIR = "/System/Library/Fonts/Supplemental"
_CJK_FONT_NAME = "Songti SC"
_LATIN_FONT = "Arial"


def _has_cjk(text: str) -> bool:
    return bool(re.search(r"[一-鿿぀-ヿ]", text))


def _extract_audio(video: str, out_wav: Path) -> Path:
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", video, "-vn", "-ac", "1", "-ar", "16000", str(out_wav)],
                   check=True)
    return out_wav


def transcribe(media: str, model_size: str = "base", lang: Optional[str] = None) -> list[dict]:
    """返回词级时间戳 [{word,start,end}]。faster-whisper(本机 CPU)。"""
    from faster_whisper import WhisperModel  # 延迟导入，engine 无此硬依赖

    src = Path(media)
    wav = src if src.suffix == ".wav" else _extract_audio(media, WORK_DIR / "sub_audio.wav")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(wav), word_timestamps=True, language=lang,
                                      vad_filter=True)
    words: list[dict] = []
    for seg in segments:
        for w in (seg.words or []):
            t = w.word.strip()
            if t:
                words.append({"word": t, "start": float(w.start), "end": float(w.end)})
    return words


def _ts(seconds: float) -> str:
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _group(words: list[dict], max_words: int = 5, max_dur: float = 2.6) -> list[list[dict]]:
    """把词分成短句（≤max_words 且 ≤max_dur 秒，遇大停顿断句）。"""
    phrases, cur = [], []
    for w in words:
        if cur:
            gap = w["start"] - cur[-1]["end"]
            span = w["end"] - cur[0]["start"]
            if len(cur) >= max_words or span > max_dur or gap > 0.7:
                phrases.append(cur)
                cur = []
        cur.append(w)
    if cur:
        phrases.append(cur)
    return phrases


def build_ass(words: list[dict], W: int, H: int) -> str:
    """词级时间戳 → ASS \\k 卡拉OK（当前词高亮）。竖屏字幕抬高避开手机 UI。"""
    cjk = _has_cjk(" ".join(w["word"] for w in words))
    font = _CJK_FONT_NAME if cjk else _LATIN_FONT
    fontsize = max(28, round(H * 0.045))
    marginv = round(H * 0.20)                 # 抬高，避开 9:16 底部 UI
    # ASS 颜色 &HAABBGGRR：Primary(已唱/当前)=黄, Secondary(未唱)=白, Outline=黑
    head = (
        "[Script Info]\nScriptType: v4.00+\n"
        f"PlayResX: {W}\nPlayResY: {H}\nWrapStyle: 2\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: K,{font},{fontsize},&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,"
        f"1,0,0,0,100,100,0,0,1,4,1,2,60,60,{marginv},1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    lines = []
    for phrase in _group(words):
        start, end = phrase[0]["start"], phrase[-1]["end"]
        prev_end = start
        text = ""
        for w in phrase:
            gap_cs = max(0, round((w["start"] - prev_end) * 100))
            dur_cs = max(1, round((w["end"] - w["start"]) * 100))
            if gap_cs:
                text += f"{{\\k{gap_cs}}}"
            sep = "" if cjk else " "
            text += f"{{\\k{dur_cs}}}{w['word']}{sep}"
            prev_end = w["end"]
        lines.append(f"Dialogue: 0,{_ts(start)},{_ts(end)},K,,0,0,0,,{text.strip()}")
    return head + "\n".join(lines) + "\n"


def burn(video: str, ass_path: Path, out: Path, cjk: bool = False) -> Path:
    """用 libass ass 滤镜把 ASS 烧进画面。"""
    ass_arg = f"ass=f='{ass_path}'"
    if cjk:
        ass_arg += f":fontsdir='{_CJK_FONT_DIR}'"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", video,
                    "-vf", ass_arg, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                    "-pix_fmt", "yuv420p", "-c:a", "copy", str(out)], check=True)
    return out


def add_subtitles(video: str, out: str, model_size: str = "base",
                  lang: Optional[str] = None, log=lambda m: None) -> dict:
    """成片 → 逐字字幕成片。返回 {words, out, skipped}。"""
    log("转录中（faster-whisper 词级）…")
    words = transcribe(video, model_size=model_size, lang=lang)
    if len(words) < 2:
        log(f"未检测到足够语音（{len(words)} 词），跳过字幕")
        return {"words": len(words), "out": video, "skipped": True}
    log(f"转录到 {len(words)} 词，生成 ASS 卡拉OK…")
    # 取成片尺寸
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height", "-of", "csv=p=0", video],
                           capture_output=True, text=True).stdout.strip()
    W, H = (int(x) for x in probe.split(",")[:2]) if "," in probe else (720, 1280)
    ass_text = build_ass(words, W, H)
    cjk = _has_cjk(" ".join(w["word"] for w in words))
    ass_path = WORK_DIR / "subtitles.ass"
    ass_path.write_text(ass_text, encoding="utf-8")
    log("烧录字幕…")
    burn(video, ass_path, Path(out), cjk=cjk)
    log(f"字幕成片 → {Path(out).name}")
    return {"words": len(words), "out": out, "skipped": False}


def main():
    ap = argparse.ArgumentParser(description="Open Edit — subtitles (Whisper 逐字字幕烧录)")
    ap.add_argument("video", help="输入成片")
    ap.add_argument("--out", default=str(WORK_DIR / "subtitled.mp4"))
    ap.add_argument("--model", default="base", help="faster-whisper 模型 (tiny/base/small/medium)")
    ap.add_argument("--lang", default=None, help="语言代码(zh/en…)，默认自动")
    args = ap.parse_args()
    r = add_subtitles(args.video, args.out, args.model, args.lang,
                      log=lambda m: print("  " + m, file=sys.stderr))
    print(args.out if not r["skipped"] else args.video)


if __name__ == "__main__":
    main()
