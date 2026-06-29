"""后台 job worker（Phase 1 = 线程池；生产 = Temporal durable 工作流）。

流水线：planning(选风格) → generating(plan_edl 调生成) → rendering(render_edl) → done。
积分：跑前 reserve gate（余额≥预算），跑中按 EDL 实际 spend，结束 settle。
"""

from __future__ import annotations

import json
import traceback
from concurrent.futures import ThreadPoolExecutor

from .config import WORK_DIR, WORKER_CONCURRENCY
from .db import SessionLocal
from .models import RenderJob, Project, Asset
from . import credits, orchestrator
from .analyze import analyze_assets
from .storage import storage

# engine（config 已加 sys.path）
from engine.build_edl import plan_edl, probe_duration
from engine.render import render_edl

_executor = ThreadPoolExecutor(max_workers=WORKER_CONCURRENCY, thread_name_prefix="oe-worker")


def enqueue(job_id: str) -> None:
    _executor.submit(_run, job_id)


def _set(session, job: RenderJob, *, status=None, progress=None):
    if status:
        job.status = status
    if progress:
        job.progress = progress
        print(f"[job {job.id[:8]}] {status or job.status}: {progress}", flush=True)
    session.commit()


def _run(job_id: str) -> None:
    session = SessionLocal()
    try:
        job = session.get(RenderJob, job_id)
        if not job:
            return
        project = session.get(Project, job.project_id)
        assets = session.query(Asset).filter(Asset.project_id == project.id).all()
        uploads = [str(storage.local_path(a.storage_key)) for a in assets if a.kind == "video"]
        kinds = [a.kind for a in assets]

        # 1) 看素材 + 选风格 + 拆 shot-plan（AI 导演）
        _set(session, job, status="planning", progress="分析素材…")
        footage = analyze_assets(uploads) if uploads else {"assets": [], "aggregate": {}}
        decision = orchestrator.direct(job.style_id, project.prompt, footage, job.target_duration)
        style_file = decision["style_file"]
        directives = decision.get("directives", "")
        shots = decision.get("shots")
        job.style_id = style_file
        _set(session, job, progress=f"导演[{decision['source']}] 选 {style_file}"
                                    f"{f'，排 {len(shots)} 镜头' if shots else ''}：{decision['reason']}")

        # 2) 烧钱前 gate（余额需 ≥ 预算上限）
        credits.reserve(session, job.org_id, job.budget_usd)
        job.reserve_usd = job.budget_usd

        # 3) 生成 + 规划 EDL（带导演 shot-plan + 创作指令 + 调色标准）
        _set(session, job, status="generating", progress="生成镜头 + 规划 EDL…")
        upload_features = {a["path"]: a for a in footage.get("assets", []) if a.get("path")}
        edl, stats = plan_edl(
            style=style_file, prompt=project.prompt, duration=job.target_duration,
            uploads=uploads, provider_name=job.provider, extra_directives=directives,
            shot_plan=shots, grade_scope="auto", upload_features=upload_features,
            video_model=(job.video_model or None),
            log=lambda m: _set(session, job, progress=m),
        )
        edl["director"] = {"style": style_file, "reason": decision["reason"],
                           "directives": directives, "source": decision["source"],
                           "planned_by": stats.get("planned_by"),
                           "shots_planned": len(shots) if shots else 0,
                           "footage": footage.get("aggregate", {})}
        job.edl_json = json.dumps(edl, ensure_ascii=False)

        # 4) 记账（按 EDL 实际生成花费）
        spent = credits.settle_from_edl(session, job.org_id, job.id, edl)
        job.spent_usd = spent
        session.commit()

        # 5) 渲染成片
        _set(session, job, status="rendering", progress="FFmpeg 渲染中…")
        out_path = WORK_DIR / job.id / "final.mp4"
        render_edl(edl, out_path, workdir=WORK_DIR / job.id / "norm",
                   log=lambda m: _set(session, job, progress=m))
        final_path = out_path

        # 5b) 可选：逐字字幕（对最终成片音轨转录 → ASS 卡拉OK → 烧录；在配乐前做，转录干净音轨）
        if job.subtitles:
            from engine.subtitles import add_subtitles
            sub_path = WORK_DIR / job.id / "final_sub.mp4"
            r = add_subtitles(str(final_path), str(sub_path),
                              lang=(job.subtitle_lang or None),
                              log=lambda m: _set(session, job, progress=m))
            if not r["skipped"]:
                final_path = sub_path

        # 5c) 可选：自动配乐（复用策展曲库，按 director 的 music_category，人声下垫底）
        if job.music:
            from engine.music import add_music
            cat = job.music_category or decision.get("music_category") or ""
            music_path = WORK_DIR / job.id / "final_music.mp4"
            r = add_music(str(final_path), str(music_path), category=cat,
                          log=lambda m: _set(session, job, progress=m))
            if not r.get("skipped"):
                final_path = music_path
                edl.setdefault("director", {})["music"] = {
                    "category": r.get("category"), "track": r.get("track"),
                    "attribution": r.get("attribution")}
                job.edl_json = json.dumps(edl, ensure_ascii=False)

        key = storage.put(str(final_path), f"renders/{job.id}.mp4")
        job.output_key = key
        job.duration_s = round(probe_duration(str(final_path)), 2)
        _set(session, job, status="done", progress=f"完成 {job.duration_s}s, 花费 ${spent:.2f}")

    except Exception as e:
        session.rollback()
        job = session.get(RenderJob, job_id)
        if job:
            job.status = "failed"
            job.error = f"{type(e).__name__}: {e}"
            job.progress = "失败"
            session.commit()
        print(f"[job {job_id[:8]}] FAILED\n{traceback.format_exc()}", flush=True)
    finally:
        session.close()
