"""FastAPI 应用 —— Open Edit v2 SaaS 后端（Phase 1）。

跑：  cd open-edit && backend/.venv/bin/uvicorn backend.app.main:app --reload
文档：http://127.0.0.1:8000/docs   （OpenAPI → iOS/web 生成 client）
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import DEFAULT_PROVIDER, SEED_CREDITS_USD
from .db import SessionLocal, init_db
from .models import Organization, User, Project, Asset, RenderJob
from . import credits, orchestrator, worker
from .storage import storage
from .schemas import (MeOut, TopupIn, ProjectCreate, ProjectOut, AssetOut,
                      RenderCreate, JobOut, StyleOut)
from engine.build_edl import probe_duration

app = FastAPI(title="Open Edit API", version="0.1.0",
              description="生成即核心的 AI 电影短片后端：上传→选风格→生成→风格化剪辑调色→成片")


# ── DB 依赖 ──────────────────────────────────────────────
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def default_org(db: Session) -> Organization:
    org = db.execute(select(Organization)).scalars().first()
    if not org:
        raise HTTPException(500, "未初始化 org")
    return org


@app.on_event("startup")
def _startup():
    init_db()
    db = SessionLocal()
    try:
        org = db.execute(select(Organization)).scalars().first()
        if not org:
            org = Organization(name="default-org")
            db.add(org)
            db.flush()
            db.add(User(org_id=org.id, email="dev@open-edit.local"))
            db.commit()
            credits.topup(db, org.id, SEED_CREDITS_USD, note="seed")
            print(f"[startup] seeded org {org.id[:8]} + ${SEED_CREDITS_USD} credits", flush=True)
    finally:
        db.close()


# ── 账户 / 积分 ──────────────────────────────────────────
@app.get("/health")
def health():
    return {"ok": True}


@app.get("/me", response_model=MeOut)
def me(db: Session = Depends(get_db)):
    org = default_org(db)
    user = db.execute(select(User).where(User.org_id == org.id)).scalars().first()
    return MeOut(org_id=org.id, email=user.email if user else "",
                 balance_usd=credits.balance(db, org.id))


@app.post("/credits/topup", response_model=MeOut)
def topup(body: TopupIn, db: Session = Depends(get_db)):
    org = default_org(db)
    credits.topup(db, org.id, body.amount_usd)
    user = db.execute(select(User).where(User.org_id == org.id)).scalars().first()
    return MeOut(org_id=org.id, email=user.email if user else "",
                 balance_usd=credits.balance(db, org.id))


# ── 风格库 ───────────────────────────────────────────────
@app.get("/styles", response_model=list[StyleOut])
def styles():
    return orchestrator.list_profiles()


# ── 项目 ─────────────────────────────────────────────────
@app.post("/projects", response_model=ProjectOut)
def create_project(body: ProjectCreate, db: Session = Depends(get_db)):
    org = default_org(db)
    p = Project(org_id=org.id, title=body.title, style_id=body.style_id, prompt=body.prompt)
    db.add(p)
    db.commit()
    return p


@app.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: str, db: Session = Depends(get_db)):
    p = db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "项目不存在")
    return p


@app.post("/projects/{project_id}/assets", response_model=AssetOut)
async def upload_asset(project_id: str, file: UploadFile = File(...),
                       db: Session = Depends(get_db)):
    p = db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "项目不存在")
    suffix = Path(file.filename or "upload.mp4").suffix or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    kind = "image" if suffix.lower() in (".jpg", ".jpeg", ".png", ".webp") else "video"
    key = storage.put(tmp_path, f"assets/{project_id}/{Path(tmp_path).name}")
    dur = probe_duration(str(storage.local_path(key))) if kind == "video" else 0.0
    Path(tmp_path).unlink(missing_ok=True)
    a = Asset(project_id=project_id, kind=kind, storage_key=key,
              filename=file.filename or "", duration_s=round(dur, 2))
    db.add(a)
    db.commit()
    return a


# ── 渲染 job ─────────────────────────────────────────────
def _job_out(job: RenderJob) -> JobOut:
    summary = None
    director = None
    if job.edl_json:
        try:
            edl = json.loads(job.edl_json)
            clips = edl.get("clips", [])
            n_up = sum(1 for c in clips if c.get("origin") == "upload")
            summary = {"clips": len(clips), "uploads": n_up,
                       "generated": len(clips) - n_up,
                       "dissolves": sum(1 for c in clips
                                        if c.get("transition_in", {}).get("type") == "dissolve")}
            director = edl.get("director")
        except Exception:
            summary = None
    return JobOut(
        id=job.id, status=job.status, provider=job.provider, style_id=job.style_id,
        target_duration=job.target_duration, reserve_usd=job.reserve_usd,
        spent_usd=job.spent_usd, duration_s=job.duration_s, progress=job.progress,
        error=job.error, edl_summary=summary, director=director,
        output_url=f"/jobs/{job.id}/output" if job.status == "done" else None,
    )


@app.post("/projects/{project_id}/render", response_model=JobOut)
def create_render(project_id: str, body: RenderCreate, db: Session = Depends(get_db)):
    p = db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "项目不存在")
    org = default_org(db)
    if body.provider not in ("mock", "fal"):
        raise HTTPException(400, "provider 仅支持 mock | fal")
    job = RenderJob(
        project_id=project_id, org_id=org.id,
        provider=body.provider or DEFAULT_PROVIDER,
        style_id=body.style_id or p.style_id,
        target_duration=body.target_duration, budget_usd=body.budget_usd,
        subtitles=body.subtitles, subtitle_lang=body.subtitle_lang or "",
        music=body.music, music_category=body.music_category or "",
        video_model=body.video_model or "",
        status="queued", progress="排队中…",
    )
    db.add(job)
    db.commit()
    worker.enqueue(job.id)
    return _job_out(job)


@app.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(RenderJob, job_id)
    if not job:
        raise HTTPException(404, "job 不存在")
    return _job_out(job)


@app.get("/jobs/{job_id}/output")
def job_output(job_id: str, db: Session = Depends(get_db)):
    job = db.get(RenderJob, job_id)
    if not job or job.status != "done" or not job.output_key:
        raise HTTPException(404, "成片未就绪")
    path = storage.local_path(job.output_key)
    if not path.exists():
        raise HTTPException(404, "成片文件丢失")
    return FileResponse(str(path), media_type="video/mp4", filename=f"{job_id}.mp4")
