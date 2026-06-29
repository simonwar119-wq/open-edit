"""编排层 —— 「AI 导演」：看素材 + 读意图 → 选风格 + 给创作指令 + 规划缺口。

plan() 是统一入口：
  - 用户显式指定风格 → 直接用
  - "auto" + 有 LLM → AI 导演（footage 特征 + prompt → 选风格 + creative_directives）
  - "auto" + 无 LLM → 启发式关键词兜底（系统始终可跑）
生产把 footage 升级成更强 Vision，把 LLM 换成更强模型，接口不变。
"""

from __future__ import annotations

import json

from engine import PROFILES_DIR     # config 已把 open-edit 加进 sys.path
from engine.music import STYLE_TO_CATEGORY
from .llm import get_llm


def list_profiles() -> list[dict]:
    out = []
    for f in sorted(PROFILES_DIR.glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        out.append({"id": d.get("id", f.stem), "file": f.stem,
                    "display_name": d.get("display_name", f.stem),
                    "inspiration": d.get("inspiration", ""),
                    "asl_seconds": d.get("pacing", {}).get("asl_seconds"),
                    "named_look": d.get("color", {}).get("palette_descriptor", {}).get("named_look")})
    return out


# ── 启发式兜底（无 LLM 时） ────────────────────────────────
_KEYWORDS = {
    "fincher-inspired-v1": ["冷", "暗", "高级", "悬疑", "控制", "克制", "夜", "金属",
                            "moody", "dark", "cold", "noir", "牛排", "厚重"],
    "wes-anderson-inspired-v1": ["暖", "粉", "对称", "可爱", "童趣", "甜", "复古", "明亮",
                                 "pastel", "symmetr", "cute", "下午茶", "甜品", "马卡龙"],
}


def choose_style_heuristic(prompt: str) -> tuple[str, str]:
    profiles = list_profiles()
    if not profiles:
        raise RuntimeError("没有可用风格 profile（engine/profiles/ 为空）")
    p = (prompt or "").lower()
    best, best_score, reason = profiles[0]["file"], -1, "默认（无明显信号）"
    for prof in profiles:
        score = sum(1 for k in _KEYWORDS.get(prof["id"], []) if k.lower() in p)
        if score > best_score:
            best, best_score = prof["file"], score
            reason = (f"命中 {score} 个 {prof['display_name']} 关键词" if score > 0
                      else "默认（无明显信号）")
    return best, reason


# ── AI 导演（有 LLM 时）：选风格 + 拆完整 shot-plan ────────
def _ai_direct(llm, prompt: str, footage: dict, profiles: list[dict],
               target_duration: float, forced_style: str | None) -> dict | None:
    valid_files = {p["file"] for p in profiles}
    catalog = [{"style_file": p["file"], "风格": p["display_name"], "调色": p["named_look"],
                "平均镜头s": p["asl_seconds"], "说明": p["inspiration"]} for p in profiles]
    system = (
        "你是电影短片的 AI 导演。先（未指定时）选一个风格，再把这条片子拆成一份完整 shot-plan："
        "每个镜头的角色/时长/景别/用上传素材还是生成/生成镜头的画面描述/入转场。"
        "让上传素材与生成镜头有机配合，节奏贴近该风格的平均镜头时长，转场克制。"
        "只输出一个 JSON 对象，不要多余文字。"
    )
    ask = {
        "创作意图": prompt,
        "目标时长秒": target_duration,
        "素材画面特征": footage,  # 含每条 asset 的 duration/tone/pace → 知道有多少真实素材可用
        "可选风格库": catalog,
        "指定风格": forced_style or "（未指定，请你选）",
        "要求输出": {
            "style_file": "风格库里的 style_file（已指定就回显）",
            "reason": "选择/编排理由（一句）",
            "creative_directives": "整体创作指令：光线/运镜/色调/质感（一句）",
            "shots": [{"role": "hook|body|climax|close", "source": "upload|generate",
                       "duration_s": 3.5, "shot_scale": "WS|MS|CU",
                       "prompt": "该镜头画面描述（generate 必填）",
                       "transition_in": {"type": "cut|dissolve", "duration": 0.5}}],
            "music_category": "tech|warm|energetic|cinematic 之一（配乐情绪）",
        },
        "约束": ["shots 总时长≈目标时长", "首镜 transition 必须 cut", "dissolve 少用",
                "有多少上传素材尽量用，不够的用 generate 补", "镜头数≈目标时长/该风格平均镜头时长"],
    }
    try:
        r = llm.complete_json(system, json.dumps(ask, ensure_ascii=False))
    except Exception as e:
        print(f"[orchestrator] AI 导演失败，回退: {type(e).__name__}: {e}", flush=True)
        return None
    sf = forced_style or r.get("style_file")
    if sf not in valid_files:
        for p in profiles:
            if sf in (p["id"], p["display_name"]):
                sf = p["file"]
                break
    if sf not in valid_files:
        return None
    shots = r.get("shots")
    shots = shots if isinstance(shots, list) and shots else None
    return {"style_file": sf, "reason": r.get("reason", ""),
            "directives": r.get("creative_directives", ""), "shots": shots,
            "music_category": r.get("music_category") or STYLE_TO_CATEGORY.get(sf, "cinematic"),
            "source": f"ai:{llm.name}"}


def direct(style_id: str, prompt: str, footage: dict | None = None,
           target_duration: float = 16.0) -> dict:
    """统一入口。返回 {style_file, reason, directives, shots, source}。
    shots=None 时由 plan_edl 自动排镜（确定性兜底）。"""
    profiles = list_profiles()
    files = {p["file"]: p for p in profiles}
    ids = {p["id"]: p for p in profiles}

    forced = None
    if style_id and style_id != "auto":
        if style_id in files:
            forced = style_id
        elif style_id in ids:
            forced = ids[style_id]["file"]
        else:
            raise ValueError(f"未知风格: {style_id}（可用: {list(files)}）")

    llm = get_llm()
    if llm:
        r = _ai_direct(llm, prompt, footage or {}, profiles, target_duration, forced)
        if r:
            return r

    # 无 LLM / AI 失败 → 兜底
    if forced:
        return {"style_file": forced, "reason": "用户指定", "directives": "", "shots": None,
                "music_category": STYLE_TO_CATEGORY.get(forced, "cinematic"), "source": "explicit"}
    f, reason = choose_style_heuristic(prompt)
    return {"style_file": f, "reason": reason, "directives": "", "shots": None,
            "music_category": STYLE_TO_CATEGORY.get(f, "cinematic"), "source": "heuristic"}
