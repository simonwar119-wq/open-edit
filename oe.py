#!/usr/bin/env python3
"""oe — Open Edit 本地统一 CLI（给 agent 调用的工具）。

把整条流水线收口成一个命令：分析素材 → AI 导演(选风格+排镜) → 生成补镜 →
风格化调色(保上传原色) → 组接 → 可选逐字字幕 → 可选自动配乐。

设计为 agent 友好：所有进度/日志走 stderr，最终结构化结果以 JSON 打到 stdout。

子命令：
  oe styles                                 列出可用导演风格(JSON)
  oe analyze <video...>                      素材画面特征(JSON)
  oe plan    --prompt ... [opts]             只规划出 EDL(不渲染)
  oe make    --prompt ... [opts]             一条龙：规划→渲染→[字幕]→[配乐]→成片
  oe render  <edl.json> [--subtitles] [--music]
  oe subtitle <video> [--out] [--lang]
  oe music    <video> [--category] [--out]

常用 opts（plan/make）：
  --prompt "一句话"            必填，成片主题
  --style auto|fincher-inspired|wes-anderson-inspired   默认 auto(导演选)
  --uploads a.mp4 b.mp4        用户素材(可多个；不给则全部生成)
  --duration 16                目标秒数
  --provider mock|fal          mock=离线零成本；fal=真生成(花钱)
  --video-model seedance-2.0-fast|seedance-2.0|kling-hq  fal 模型档
  --subtitles                  逐字字幕(Whisper 烧录)
  --music [--music-category tech|warm|energetic|cinematic]  自动配乐
  --out film.mp4               成片路径

真生成需 export FAL_API_KEY；真 LLM 导演需 OPENEDIT_LLM_PROVIDER+key（缺则启发式兜底）。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import WORK_DIR                                  # noqa: E402
from engine.build_edl import plan_edl, probe_duration       # noqa: E402
from engine.render import render_edl                         # noqa: E402
from engine.subtitles import add_subtitles                   # noqa: E402
from engine.music import add_music                            # noqa: E402
from engine.character import train_character, load_character, list_characters  # noqa: E402
from engine import edl as edl_mod                             # noqa: E402
# 共享"导演大脑"（CLI 与 SaaS 后端共用）
from backend.app.analyze import analyze_assets               # noqa: E402
from backend.app.orchestrator import direct, list_profiles   # noqa: E402


def log(m: str) -> None:
    print(m, file=sys.stderr, flush=True)


def emit(obj: dict) -> None:
    """结构化结果 → stdout（agent 解析）。"""
    print(json.dumps(obj, ensure_ascii=False, indent=2))


# ── 导演 + 规划 ───────────────────────────────────────────
def build_with_director(args) -> tuple[dict, dict, dict, str]:
    uploads = [u for u in (args.uploads or []) if Path(u).exists()]
    footage = analyze_assets(uploads) if uploads else {"assets": [], "aggregate": {}}
    log(f"▸ 分析素材 {len(uploads)} 条 …")
    character = load_character(args.character) if getattr(args, "character", None) else None
    if character:
        log(f"▸ 角色: {character['name']}（trigger='{character['trigger_word']}'，生成镜头将保持同一张脸）")
    decision = direct(args.style, args.prompt, footage, args.duration)
    n_shots = len(decision["shots"]) if decision.get("shots") else 0
    extra = f"，排 {n_shots} 镜头" if n_shots else ""
    log(f"▸ 导演[{decision['source']}] 选 {decision['style_file']}{extra}：{decision['reason']}")

    upload_features = {a["path"]: a for a in footage.get("assets", []) if a.get("path")}
    edl, stats = plan_edl(
        style=decision["style_file"], prompt=args.prompt, duration=args.duration,
        uploads=uploads, provider_name=args.provider,
        extra_directives=decision.get("directives", ""), shot_plan=decision.get("shots"),
        grade_scope=args.grade_scope, upload_features=upload_features,
        video_model=args.video_model, character=character, log=lambda m: log("  " + m),
    )
    edl["director"] = {"style": decision["style_file"], "reason": decision["reason"],
                       "directives": decision.get("directives", ""), "source": decision["source"],
                       "music_category": decision.get("music_category"),
                       "footage": footage.get("aggregate", {})}
    edl_path = args.edl_out or str(WORK_DIR / "oe.edl.json")
    edl_mod.save(edl, edl_path)
    return edl, decision, stats, edl_path


# ── 子命令 ────────────────────────────────────────────────
def cmd_styles(args):
    emit({"styles": list_profiles()})


def cmd_analyze(args):
    emit(analyze_assets(args.videos))


def cmd_plan(args):
    edl, decision, stats, edl_path = build_with_director(args)
    emit({"edl": edl_path, "director": edl["director"], "stats": stats})


def cmd_render(args):
    out = args.out or str(WORK_DIR / "oe_render.mp4")
    render_edl(args.edl, out, log=lambda m: log("  " + m))
    final, subi, musi = _post(out, args)
    emit({"output": final, "duration_s": probe_duration(final), "subtitles": subi, "music": musi})


def cmd_make(args):
    edl, decision, stats, edl_path = build_with_director(args)
    out = args.out or str(WORK_DIR / "oe_film.mp4")
    log("▸ 渲染中 …")
    render_edl(edl, out, log=lambda m: log("  " + m))
    final, subi, musi = _post(out, args, default_music_cat=decision.get("music_category"))
    emit({"output": final, "duration_s": round(probe_duration(final), 2),
          "style": decision["style_file"], "director": edl["director"],
          "clips": stats["clips"], "generated": stats["generated"], "uploads": stats["uploads"],
          "cost_usd": stats["spent_usd"], "edl": edl_path,
          "subtitles": subi, "music": musi})


def cmd_subtitle(args):
    out = args.out or str(WORK_DIR / "oe_sub.mp4")
    r = add_subtitles(args.video, out, model_size=args.model, lang=args.lang,
                      log=lambda m: log("  " + m))
    emit({"output": r["out"], "words": r.get("words"), "skipped": r.get("skipped")})


def cmd_music(args):
    out = args.out or str(WORK_DIR / "oe_music.mp4")
    r = add_music(args.video, out, category=args.category, log=lambda m: log("  " + m))
    emit(r)


def cmd_animate(args):
    """一张照片 + 一句场景 → 视频（图生视频 i2v）。"""
    import shutil
    import subprocess as sp
    from engine.providers import get_provider
    from engine.providers.base import GenSpec

    probe = sp.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                    "stream=width,height", "-of", "csv=p=0", args.image],
                   capture_output=True, text=True).stdout.strip()
    try:
        W, H = (int(x) for x in probe.split(",")[:2])
    except Exception:
        W, H = 720, 1280
    log(f"▸ 图生视频[{args.provider}/{args.model}] {Path(args.image).name} ({W}x{H}) — 约5分钟 …")
    provider = get_provider(args.provider)
    spec = GenSpec(prompt=args.prompt, kind="i2v", duration_s=args.duration,
                   width=W, height=H, model=args.model, image_path=args.image)
    res = provider.submit(spec)
    final = args.out or str(WORK_DIR / "oe_animate.mp4")
    shutil.copy(res.local_path, final)
    emit({"output": final, "model": res.model, "cost_usd": res.cost_usd,
          "duration_s": res.duration_s, "seed_image": args.image,
          "commercial_ok": res.commercial_ok})


def cmd_train_character(args):
    """多角度照片 → 训练身份角色模型（FLUX LoRA，约 $2）。"""
    prof = train_character(args.name, args.photos, trigger_word=args.trigger,
                           steps=args.steps, log=lambda m: log("  " + m))
    emit({"character": prof["name"], "trigger_word": prof["trigger_word"],
          "lora_url": prof["lora_url"], "n_photos": prof["n_photos"],
          "usage": f"./oe make --character {prof['slug']} --provider fal --prompt ..."})


def cmd_characters(args):
    emit({"characters": list_characters()})


def _post(video: str, args, default_music_cat: str | None = None):
    """渲染后处理：字幕(先，转录干净音轨) → 配乐。返回 (final_path, sub_info, music_info)。"""
    final, subi, musi = video, None, None
    if getattr(args, "subtitles", False):
        log("▸ 逐字字幕 …")
        sub_out = str(WORK_DIR / "oe_film_sub.mp4")
        r = add_subtitles(final, sub_out, lang=getattr(args, "lang", None),
                          log=lambda m: log("  " + m))
        subi = {"words": r.get("words"), "skipped": r.get("skipped")}
        if not r.get("skipped"):
            final = sub_out
    if getattr(args, "music", False):
        log("▸ 自动配乐 …")
        mus_out = str(WORK_DIR / "oe_film_music.mp4")
        cat = getattr(args, "music_category", None) or default_music_cat
        r = add_music(final, mus_out, category=cat, log=lambda m: log("  " + m))
        musi = {k: r.get(k) for k in ("category", "track", "attribution", "skipped")}
        if not r.get("skipped"):
            final = mus_out
    return final, subi, musi


# ── argparse ──────────────────────────────────────────────
def _add_plan_opts(p):
    p.add_argument("--prompt", required=True)
    p.add_argument("--style", default="auto")
    p.add_argument("--uploads", nargs="*", default=[])
    p.add_argument("--duration", type=float, default=16.0)
    p.add_argument("--provider", default="mock", choices=["mock", "fal"])
    p.add_argument("--video-model", dest="video_model", default=None)
    p.add_argument("--grade-scope", dest="grade_scope", default="auto",
                   choices=["auto", "all", "none"])
    p.add_argument("--character", default=None,
                   help="身份角色(slug，见 ./oe characters)；生成镜头保持同一张脸")
    p.add_argument("--edl-out", dest="edl_out", default=None)


def main():
    ap = argparse.ArgumentParser(prog="oe", description="Open Edit 本地统一 CLI（agent 工具）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("styles").set_defaults(func=cmd_styles)

    pa = sub.add_parser("analyze")
    pa.add_argument("videos", nargs="+")
    pa.set_defaults(func=cmd_analyze)

    pp = sub.add_parser("plan")
    _add_plan_opts(pp)
    pp.set_defaults(func=cmd_plan)

    pm = sub.add_parser("make")
    _add_plan_opts(pm)
    pm.add_argument("--subtitles", action="store_true")
    pm.add_argument("--lang", default=None)
    pm.add_argument("--music", action="store_true")
    pm.add_argument("--music-category", dest="music_category", default=None,
                    choices=[None, "tech", "warm", "energetic", "cinematic"])
    pm.add_argument("--out", default=None)
    pm.set_defaults(func=cmd_make)

    pr = sub.add_parser("render")
    pr.add_argument("edl")
    pr.add_argument("--out", default=None)
    pr.add_argument("--subtitles", action="store_true")
    pr.add_argument("--lang", default=None)
    pr.add_argument("--music", action="store_true")
    pr.add_argument("--music-category", dest="music_category", default=None)
    pr.set_defaults(func=cmd_render)

    ps = sub.add_parser("subtitle")
    ps.add_argument("video")
    ps.add_argument("--out", default=None)
    ps.add_argument("--model", default="base")
    ps.add_argument("--lang", default=None)
    ps.set_defaults(func=cmd_subtitle)

    pmu = sub.add_parser("music")
    pmu.add_argument("video")
    pmu.add_argument("--out", default=None)
    pmu.add_argument("--category", default=None,
                     choices=[None, "tech", "warm", "energetic", "cinematic"])
    pmu.set_defaults(func=cmd_music)

    pan = sub.add_parser("animate")          # 一张照片 + 场景 → 视频
    pan.add_argument("image")
    pan.add_argument("--prompt", required=True)
    pan.add_argument("--provider", default="fal", choices=["fal", "mock"])
    pan.add_argument("--model", default="kling-i2v")
    pan.add_argument("--duration", type=float, default=5.0)
    pan.add_argument("--out", default=None)
    pan.set_defaults(func=cmd_animate)

    ptc = sub.add_parser("train-character")  # 多角度照片 → 身份角色模型
    ptc.add_argument("photos", nargs="+")
    ptc.add_argument("--name", required=True)
    ptc.add_argument("--trigger", default=None)
    ptc.add_argument("--steps", type=int, default=1000)
    ptc.set_defaults(func=cmd_train_character)

    sub.add_parser("characters").set_defaults(func=cmd_characters)

    args = ap.parse_args()
    try:
        args.func(args)
    except Exception as e:
        emit({"error": f"{type(e).__name__}: {e}"})
        sys.exit(1)


if __name__ == "__main__":
    main()
