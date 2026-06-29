"""prompt_kit — open-edit 的 prompt 纪律层（抄自 Higgsfield MCSLA/DISCIPLINE，工程化）。

把"博主秘籍"变成代码：MCSLA 五层公式 + 真实感词库 + 反 slop 替换 +
身份/运动分块 + Seedance 六槽/五模式 + 相机预设查询。

研究来源：_research/higgsfield-2026-06-28/04（OSideMedia/higgsfield-ai-prompt-skill, MIT）。

用法：
    from engine.prompt_kit import mcsla, camera, seedance_i2v, realism_suffix, lint_terms
    p = mcsla(camera="Dolly In", subject="a man in a black turtleneck",
              look="candlelit hall, warm low-key, shallow DoF", action="walks slowly toward camera")
"""
from __future__ import annotations

import json
from pathlib import Path

_PRESETS_PATH = Path(__file__).resolve().parent.parent / "taxonomy" / "dop_camera_presets.json"
_PRESETS = json.loads(_PRESETS_PATH.read_text(encoding="utf-8"))
_BY_NAME = {p["name"].lower(): p for p in _PRESETS["presets"]}

# ── 真实感词库（正向锚 / 禁用词）──────────────────────────────
REALISM_POSITIVE = (
    "photorealistic, raw photo, natural skin texture with visible pores, subtle sheen, "
    "uneven light falloff, 35mm film grain, unretouched"
)
REALISM_LIGHTING_HINTS = "single side-light or window light, golden hour, low-key warm"
# 这些词触发"塑料脸/CGI 感"，构造 prompt 时禁用
PLASTIC_TRIGGERS = {"flawless", "perfect skin", "8k", "ultra realistic", "ultra-realistic",
                    "hyperrealistic", "airbrushed", "smooth skin", "beautiful", "stunning"}

# ── 反 slop 替换表（Higgsfield anti-slop，原文）──────────────
SLOP_REPLACEMENTS = {
    "beautiful": "（删，改描述具体视觉）",
    "stunning": "（删，改描述具体视觉）",
    "amazing": "（删，改描述具体视觉）",
    "epic": "large-scale / sweeping / towering",
    "dynamic": "fast-tracking / whip-pan / handheld",
    "energetic": "sprinting / jumping / arms pumping",
    "cinematic camera movement": "slow dolly push / crane up / tracking shot",
    "cool transition": "match-cut / whip pan / smash cut",
}
SLOP_WORDS = set(SLOP_REPLACEMENTS) | {"gorgeous", "breathtaking", "masterpiece", "mesmerizing"}

# ── 引擎硬约束（Seedance，抄自 ENGINE-RULES）─────────────────
ENGINE_LIMITS = {
    "max_tracked_characters": 3,
    "avoid_reflections": True,           # 刀/水洼/镜子会破坏几何
    "offscreen_means_gone": True,        # 出框=隐性 cut
    "describe_visible_only": True,       # 无气味/味道/内心想法
    "one_primary_action_per_clip": True,
    "max_words": 200,
    "seedance_sweet_words": (30, 100),   # Seedance 短 prompt 赢
    "zh_max_chars": 1800,
}


def camera(name: str) -> dict:
    """按预设名取相机宏（含 prompt_fragment / best_for / face_safe）。"""
    p = _BY_NAME.get((name or "").strip().lower())
    if not p:
        raise KeyError(f"未知相机预设 '{name}'。可选见 taxonomy/dop_camera_presets.json")
    return p


def camera_fragment(name: str) -> str:
    return camera(name)["prompt_fragment"]


def camera_for_emotion(emotion: str) -> str:
    """按情绪取相机处方（emotion_sync 表）。"""
    return _PRESETS["emotion_sync"].get(emotion, _PRESETS["emotion_sync"]["calm_control"])


def realism_suffix() -> str:
    return f"{REALISM_POSITIVE}, {REALISM_LIGHTING_HINTS}"


def mcsla(*, subject: str, action: str, look: str, camera: str | None = None,
          model: str | None = None, add_realism: bool = True) -> str:
    """MCSLA 五层公式构造 prompt：Model + Camera + Subject + Look + Action。
    相机用预设名（自动展开 fragment）。返回单段 prompt 字符串。"""
    parts = []
    if subject:
        parts.append(subject.strip().rstrip("."))
    if action:
        parts.append(action.strip().rstrip("."))
    if look:
        parts.append(look.strip().rstrip("."))
    if camera:
        parts.append(f"Camera: {camera_fragment(camera)}")
    if add_realism:
        parts.append(realism_suffix())
    body = ". ".join(parts) + "."
    if model:
        body = f"[{model}] " + body
    return body


def identity_motion_blocks(*, identity: str, action: str, camera: str | None,
                           look: str, env_motion: str = "") -> dict:
    """Soul ID 必用：身份块 ⟂ 运动块物理分离，相机移动时脸才不扭。
    返回 {'identity': ..., 'motion': ...}，i2v/续镜时身份块逐字复用。"""
    motion_bits = [action.strip().rstrip(".")]
    if camera:
        motion_bits.append(f"Camera: {camera_fragment(camera)}")
    if env_motion:
        motion_bits.append(env_motion.strip().rstrip("."))
    motion_bits.append(look.strip().rstrip("."))
    return {
        "identity": identity.strip(),                       # NO motion / NO camera / NO temporal
        "motion": ". ".join(motion_bits) + ".",             # NO appearance repetition
    }


def seedance_i2v(*, action: str, camera: str | None = None, setting: str = "",
                 style: str = "", lighting: str = "") -> str:
    """Seedance 六槽 i2v：[Camera]+[Subject/Action]+[Setting]+[Style]+[Lighting]。
    i2v 只描述「动/变」的东西，不复述图里已有的静态元素。"""
    slots = []
    if camera:
        slots.append(camera_fragment(camera))
    slots.append(action.strip().rstrip("."))
    if setting:
        slots.append(setting.strip().rstrip("."))
    if style:
        slots.append(style.strip().rstrip("."))
    if lighting:
        slots.append(lighting.strip().rstrip("."))
    return ". ".join(s for s in slots if s) + "."


# Seedance 五种 prompt 模式骨架（填空模板）
SEEDANCE_MODES = {
    "reference": "[Source image role: as the main character / as the starting frame]. "
                 "[Action the subject performs]. [Environment if not visible in source]. "
                 "[Camera movement]. [Lighting cue if different from source].",
    "continuation": "[Continuing from prior clip, last frame: pose/position/gaze]. "
                    "[Identity block verbatim]. [New action that follows from the last frame]. "
                    "[Camera direction]. [Any state change].",
    "expand": "[Source frame reference]. Extend the scene [outward/upward/leftward]. "
              "[What appears in the newly revealed area]. [Preserve original subject/composition].",
    "edit": "Change [specific element] to [new state]. Keep [everything else] unchanged. "
            "[Preserve identity, composition, lighting, camera behavior].",
    "transformation": "[Subject starting state — full identity]. [Triggering cue]. "
                      "[Subject mid-transformation — observable physical change]. "
                      "[Subject ending state]. [Camera behavior across the change]. [Palette shift].",
}


def lint_terms(prompt: str) -> dict:
    """轻量预检：找出 slop 词 + 塑料触发词 + 词数。返回告警 dict（不阻断）。"""
    low = prompt.lower()
    found_slop = sorted(w for w in SLOP_WORDS if w in low)
    found_plastic = sorted(w for w in PLASTIC_TRIGGERS if w in low)
    words = len(prompt.split())
    warnings = []
    if found_slop:
        warnings.append(f"slop 词（建议替换）: {found_slop}")
    if found_plastic:
        warnings.append(f"塑料脸触发词（建议删除）: {found_plastic}")
    if words > ENGINE_LIMITS["max_words"]:
        warnings.append(f"超 {ENGINE_LIMITS['max_words']} 词（{words}）")
    return {"ok": not warnings, "words": words, "warnings": warnings,
            "slop": found_slop, "plastic": found_plastic}


if __name__ == "__main__":
    # 自检：FUSION hero 镜
    demo = mcsla(camera="Dolly In",
                 subject="a 40 year old asian man in a black turtleneck",
                 look="lavish candlelit castle banquet hall, warm low-key golden light, shallow depth of field",
                 action="walks slowly toward the camera, calm confident expression")
    print("MCSLA:\n", demo, "\n")
    print("LINT:", lint_terms(demo))
    print("\nemotion[calm_control]:", camera_for_emotion("calm_control"))
    print("presets loaded:", len(_PRESETS["presets"]))
