#!/usr/bin/env python3
"""build_edl — 模式B 反向分镜 + 缺口生成 → 产出 EDL(JSON)。

两种排镜来源：
  - shot_plan（AI 导演给的完整 shot-plan）→ LLM 决定结构，代码只做机械执行
  - 无 shot_plan → 按风格 ASL 自动排镜（确定性兜底）
两种都走同一条装配循环：upload 切片 / generate 调 provider / 铺转场 → EDL。
LLM 决定创作结构，确定性代码做切片+生成+装配（LLM 永不碰像素）。

核心逻辑在 plan_edl()，CLI 与 backend 共用。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional

from . import WORK_DIR
from .style_profile import StyleProfile
from .providers import get_provider
from .providers.base import GenSpec
from . import edl as edl_mod


def probe_duration(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def plan_durations(total: float, n: int, asl: float, lo: float, hi: float) -> list[float]:
    """把 total 秒切成 n 段，节奏围绕 asl 起伏（确定性，无随机）。"""
    lo = max(1.0, lo)
    pattern = [0.7, 1.0, 1.3, 0.85, 1.15]
    base = total / n
    raw = [max(lo, min(hi, base * pattern[i % len(pattern)])) for i in range(n)]
    scale = total / sum(raw)
    durs = [round(max(lo, d * scale), 3) for d in raw]
    diff = round(total - sum(durs), 3)
    durs[-1] = round(max(lo, durs[-1] + diff), 3)
    return durs


# 景别代码 → 生成模型能懂的词（"MS" 对图像模型是噪声）
_SCALE_WORDS = {"ECU": "extreme close-up", "CU": "close-up", "MCU": "medium close-up",
                "MS": "medium shot", "MLS": "medium long shot", "FS": "full shot",
                "LS": "long shot", "WS": "wide shot", "EWS": "extreme wide shot"}


def role_for(i: int, n: int) -> str:
    if i == 0:
        return "hook"
    if i == n - 1:
        return "close"
    if i >= n - 2:
        return "climax"
    return "body"


def _auto_shots(duration: float, asl: float, lo: float, hi: float,
                has_uploads: bool) -> list[dict]:
    """无 AI shot-plan 时的确定性排镜：upload/generate 交替。"""
    n = max(3, round(duration / asl))
    durs = plan_durations(duration, n, asl, lo, hi)
    shots = []
    for i in range(n):
        shots.append({"duration": durs[i], "role": role_for(i, n),
                      "source": "upload" if (has_uploads and i % 2 == 0) else "generate",
                      "shot_scale": "", "prompt": "", "transition_in": None})
    return shots


def _normalize_plan(shot_plan: list[dict], duration: float, lo: float, hi: float,
                    has_uploads: bool) -> list[dict]:
    """清洗 + 守卫 LLM 给的 shot-plan：钳制时长、缩放到 target、修正非法 source。"""
    shots = []
    for s in shot_plan[:16]:
        d = s.get("duration_s", s.get("duration", 0)) or 0
        try:
            d = float(d)
        except (TypeError, ValueError):
            d = 0.0
        d = max(1.0, min(hi, d if d > 0 else 3.0))
        src = s.get("source", "generate")
        if src not in ("upload", "generate"):
            src = "generate"
        if src == "upload" and not has_uploads:
            src = "generate"
        shots.append({"duration": d, "role": s.get("role", "body"), "source": src,
                      "shot_scale": s.get("shot_scale", ""), "prompt": s.get("prompt", ""),
                      "transition_in": s.get("transition_in")})
    if not shots:
        raise ValueError("空 shot-plan")
    tot = sum(x["duration"] for x in shots)
    scale = duration / tot if tot > 0 else 1.0
    for x in shots:
        x["duration"] = round(max(1.0, x["duration"] * scale), 3)
    return shots


class _UploadAllocator:
    """把多条上传素材拼成一条时间线，按需切非重叠窗口（不复用同段素材）。"""
    def __init__(self, uploads_ok: list[tuple[str, float]]):
        self.uploads = uploads_ok
        self.idx = 0
        self.offset = 0.0

    def take(self, d: float) -> Optional[tuple[str, float, float]]:
        while self.idx < len(self.uploads):
            u, udur = self.uploads[self.idx]
            if self.offset + d <= udur + 1e-3:
                win = (u, round(self.offset, 3), round(d, 3))
                self.offset += d
                return win
            self.idx += 1
            self.offset = 0.0
        return None  # 素材用尽 → 调用方改 generate


def _grade_for(origin: str, source: str, grade_scope: str,
               upload_features: Optional[dict]) -> dict:
    """调色标准 —— 决定一个 clip 该不该套风格调色。

    生成镜头/平素材 → style（套完整 CDL+LUT）。
    已调好色的上传素材 → preserve（保原色，避免二次调色变诡异，修复 qmike 问题）。
    grade_scope: auto(默认) | all(全都套) | none(都不套)。
    """
    if origin == "generated":
        return {"mode": "style"}
    if grade_scope == "all":
        return {"mode": "style"}
    if grade_scope == "none":
        return {"mode": "preserve"}
    # auto：默认保上传素材原色。饱和度不可靠（成片也可能刻意低饱和），不做自动重调色。
    # 真正的 raw/log 素材想统一调色 → 显式传 grade_scope="all"。
    # 只有"几乎纯灰"(饱和度极低 < 0.05，基本确定是 log)才破例套风格。
    feat = None
    if upload_features:
        feat = upload_features.get(source) or upload_features.get(str(Path(source).resolve()))
    sat = feat.get("saturation") if feat else None
    if sat is not None and sat < 0.05:
        return {"mode": "style"}
    return {"mode": "preserve"}


def plan_edl(
    style: str,
    prompt: str,
    duration: float = 16.0,
    uploads: Optional[list[str]] = None,
    provider_name: str = "mock",
    out_path: Optional[str] = None,
    extra_directives: str = "",
    shot_plan: Optional[list[dict]] = None,
    grade_scope: str = "auto",
    upload_features: Optional[dict] = None,
    video_model: Optional[str] = None,
    character: Optional[dict] = None,
    log: Callable[[str], None] = lambda m: None,
) -> tuple[dict, dict]:
    """规划一条 EDL。返回 (edl_dict, stats)。CLI 与 backend 共用。

    shot_plan: AI 导演给的完整排镜（None 则按风格 ASL 自动排）。
    extra_directives: 导演创作指令，注入每个生成镜头 prompt。
    """
    uploads = uploads or []
    profile = StyleProfile.load(style)
    W, H = profile.render_dims
    fps = profile.fps
    asl = profile.asl
    lo, hi = profile.shot_len_range

    provider = get_provider(provider_name)
    if provider_name == "fal":
        model = video_model or profile.preferred_model      # 可被 job/CLI 覆盖（如 kling-hq）
    else:
        model = "seedance-2.0-fast"

    uploads_ok = [(u, probe_duration(u)) for u in uploads if Path(u).exists()]
    alloc = _UploadAllocator(uploads_ok)

    min_per_scene = int(profile.get("coverage", "min_shots_per_scene", default=3))
    rule = (profile.get("transitions", "rules", default=[{}]) or [{}])[0]
    dissolve_ms = int(rule.get("duration_ms", 500))
    max_per_min = float(rule.get("max_per_minute", 2))
    dissolve_cap = max(1, int(max_per_min * duration / 60))
    dissolves_used = 0

    if shot_plan:
        shots = _normalize_plan(shot_plan, duration, lo, hi, bool(uploads_ok))
        log(f"AI 导演 shot-plan: {len(shots)} 镜头")
    else:
        shots = _auto_shots(duration, asl, lo, hi, bool(uploads_ok))
        log(f"自动排镜: {len(shots)} 镜头 (ASL {asl}s)")

    log(f"风格 {profile.display_name} ({profile.id}) | 目标 {duration}s | {W}x{H}@{fps}")

    edl = edl_mod.new_edl(profile.id, prompt, W, H, fps,
                          color=profile.get("color", default={}),
                          audio=profile.get("audio_music", default={}))
    reserve = spent = 0.0
    n = len(shots)

    for i, shot in enumerate(shots):
        d = shot["duration"]
        role = shot.get("role", "body")

        # 转场：首镜恒 cut；其余取 shot 指定或按场景边界规则，受 dissolve_cap 限制
        if i == 0:
            trans = {"type": "cut", "duration": 0.0}
        else:
            want = shot.get("transition_in") or {}
            want_diss = (want.get("type") == "dissolve") or \
                        (not want and i % min_per_scene == 0)
            if want_diss and dissolves_used < dissolve_cap:
                dur = float(want.get("duration", dissolve_ms / 1000)) if want else dissolve_ms / 1000
                trans = {"type": "dissolve", "duration": round(min(dur, 1.0), 3)}
                dissolves_used += 1
            else:
                trans = {"type": "cut", "duration": 0.0}

        win = alloc.take(d) if shot.get("source") == "upload" else None
        if win:
            u, start, dd = win
            clip = {"id": f"c{i+1}", "source": str(Path(u).resolve()),
                    "in": start, "out": round(start + dd, 3),
                    "origin": "upload", "role": role, "transition_in": trans}
        else:
            # 场景词在前(权重高)，景别展开成词，再加"相机/构图"风格(不含颜色——颜色交给LUT)
            scene = shot.get("prompt") or prompt
            scale = shot.get("shot_scale", "")
            scale_word = _SCALE_WORDS.get(scale.upper(), scale)
            bits = [scene, scale_word, profile.shot_prompt_style, extra_directives]
            shot_prompt = ", ".join(b for b in bits if b)
            # 有 character → 走 kling-hq(FLUX+LoRA 出脸 → Kling 动)，保持同一张脸
            gen_model = "kling-hq" if character else model
            spec = GenSpec(prompt=shot_prompt, kind="t2v", duration_s=d,
                           width=W, height=H, fps=fps, model=gen_model,
                           lora_url=(character or {}).get("lora_url"),
                           trigger_word=(character or {}).get("trigger_word"))
            reserve += provider.estimate_cost(spec)
            log(f"[{i+1}/{n}] 生成({provider_name}/{model}) {d}s ▸ {role} …")
            res = provider.submit(spec)
            spent += res.cost_usd
            clip = {"id": f"c{i+1}", "source": res.local_path,
                    "in": 0.0, "out": round(res.duration_s, 3),
                    "origin": "generated", "role": role, "transition_in": trans,
                    "gen": {"provider": res.provider, "model": res.model,
                            "cost_usd": res.cost_usd, "commercial_ok": res.commercial_ok,
                            "prompt": shot_prompt}}
        clip["grade"] = _grade_for(clip["origin"], clip["source"], grade_scope, upload_features)
        edl["clips"].append(clip)

    edl["cost"]["reserve_usd"] = round(reserve, 4)
    edl["cost"]["spent_usd"] = round(spent, 4)

    errs = edl_mod.validate(edl)
    if errs:
        raise ValueError("EDL 校验未通过: " + "; ".join(errs))
    if out_path:
        edl_mod.save(edl, out_path)

    n_up = sum(1 for c in edl["clips"] if c["origin"] == "upload")
    stats = {"clips": len(edl["clips"]), "uploads": n_up,
             "generated": len(edl["clips"]) - n_up, "dissolves": dissolves_used,
             "reserve_usd": round(reserve, 4), "spent_usd": round(spent, 4),
             "width": W, "height": H, "fps": fps,
             "planned_by": "ai" if shot_plan else "auto"}
    log(f"EDL {stats['clips']} 镜头 ({n_up} 上传 + {stats['generated']} 生成), "
        f"{dissolves_used} dissolve, reserve ${reserve:.2f} spent ${spent:.2f}")
    return edl, stats


def main():
    ap = argparse.ArgumentParser(description="Open Edit — build_edl (模式B 规划器)")
    ap.add_argument("--style", required=True, help="风格 profile（id 或文件名）")
    ap.add_argument("--prompt", required=True, help="成片主题/一句话")
    ap.add_argument("--duration", type=float, default=16.0, help="目标成片时长(秒)")
    ap.add_argument("--uploads", nargs="*", default=[], help="用户上传素材(本地视频路径)")
    ap.add_argument("--provider", default="mock", choices=["mock", "fal"], help="生成 provider")
    ap.add_argument("--video-model", default=None,
                    help="fal 视频模型覆盖：seedance-2.0-fast | seedance-2.0 | kling-hq")
    ap.add_argument("--out", default=str(WORK_DIR / "out.edl.json"), help="EDL 输出路径")
    args = ap.parse_args()

    def log(m):
        print("   " + m, file=sys.stderr)

    try:
        _, stats = plan_edl(args.style, args.prompt, args.duration, args.uploads,
                            args.provider, args.out, video_model=args.video_model, log=log)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ EDL → {args.out}", file=sys.stderr)
    print(args.out)


if __name__ == "__main__":
    main()
