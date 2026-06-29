"""seedance_lint — 生成前 prompt 预检（抄自 Higgsfield seedance_lint.py 思路）。

Seedance 2.0 内容过滤器是个读"语域"的语言模型：像导演描述镜头→过；像便条→挂。
这个 linter 在花钱生成前抓常见违规，把彩票税前置成本地秒级检查。

CLI：  python -m engine.seedance_lint "<prompt>" [--zh]
返回 {ok, score, errors[], warnings[]}；errors=很可能挂，warnings=建议改。
"""
from __future__ import annotations

import sys
import json
import argparse

from engine.prompt_kit import SLOP_WORDS, PLASTIC_TRIGGERS, ENGINE_LIMITS, _BY_NAME

# 多相机移动同现 = 违反"一镜一主导运镜"
_MOVE_HINTS = ["dolly", "crane", "orbit", "zoom", "pan", "tilt", "whip", "fpv", "arc",
               "tracking", "handheld", "jib", "crash"]
_CONFLICTS = [("dolly in", "dolly out"), ("crane up", "crane down"),
              ("zoom in", "zoom out"), ("pan left", "pan right")]
# "便条语域"信号（非场景描述）
_NOTE_REGISTER = ["please", "can you", "i want", "make me", "i need", "could you", "generate a video of"]


def lint(prompt: str, *, zh: bool = False) -> dict:
    low = prompt.lower()
    errors, warnings = [], []

    # 1. 语域：像便条→过滤器易拒
    for n in _NOTE_REGISTER:
        if n in low:
            errors.append(f"便条语域 '{n}'：改成导演式场景描述（描述 scene，不是请求）")

    # 2. 槽位完整度（六槽缺 3+ = flag 来源）：相机/主体/动作/场景/风格/光
    has_camera = any(h in low for h in _MOVE_HINTS) or "static" in low
    has_light = any(w in low for w in ["light", "lit", "lighting", "golden", "shadow", "glow", "candle", "neon", "sun"])
    has_style = any(w in low for w in ["cinematic", "film", "grain", "anamorphic", "35mm", "grade", "palette", "photoreal"])
    slots = {"camera": has_camera, "lighting": has_light, "style": has_style}
    missing = [k for k, v in slots.items() if not v]
    if len(missing) >= 2:
        warnings.append(f"槽位缺失 {missing}：六槽缺多个会被 flag，补全相机/光/风格")

    # 3. 冲突运镜
    for a, b in _CONFLICTS:
        if a in low and b in low:
            errors.append(f"冲突运镜同现：'{a}' + '{b}'（一镜只能一个主导运镜）")

    # 4. slop / 塑料触发
    slop = sorted(w for w in SLOP_WORDS if w in low)
    plastic = sorted(w for w in PLASTIC_TRIGGERS if w in low)
    if slop:
        warnings.append(f"slop 词: {slop}（换成具体视觉/物理）")
    if plastic:
        warnings.append(f"塑料脸触发词: {plastic}（删，会出 CGI/腊像脸）")

    # 5. 反射镜头（破坏几何）
    if any(w in low for w in ["mirror", "reflection", "reflective", "puddle"]):
        warnings.append("含反射元素（镜子/水洼）：Seedance 渲反射会破坏场景几何，尽量避开")

    # 6. 长度
    words = len(prompt.split())
    if not zh and words > ENGINE_LIMITS["max_words"]:
        errors.append(f"超 {ENGINE_LIMITS['max_words']} 词（{words}）")
    if zh and len(prompt) > ENGINE_LIMITS["zh_max_chars"]:
        errors.append(f"中文超 {ENGINE_LIMITS['zh_max_chars']} 字符（{len(prompt)}）")
    lo, hi = ENGINE_LIMITS["seedance_sweet_words"]
    if not zh and words < lo:
        warnings.append(f"偏短（{words} 词），Seedance 甜区 {lo}-{hi} 词，主体+动作放前 20-30 词")

    score = max(0, 100 - 40 * len(errors) - 10 * len(warnings))
    return {"ok": not errors, "score": score, "words": words,
            "errors": errors, "warnings": warnings}


def _main():
    ap = argparse.ArgumentParser(prog="seedance_lint")
    ap.add_argument("prompt")
    ap.add_argument("--zh", action="store_true")
    a = ap.parse_args()
    print(json.dumps(lint(a.prompt, zh=a.zh), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _main()
