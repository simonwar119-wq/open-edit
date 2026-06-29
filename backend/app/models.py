"""数据模型（plan 的核心表的 Phase 1 实现）。

organizations / users / projects / assets / render_jobs / generation_requests / credit_ledger
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, Float, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _uid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.utcnow()


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uid)
    name: Mapped[str] = mapped_column(String(200), default="default-org")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uid)
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    email: Mapped[str] = mapped_column(String(320), default="dev@open-edit.local")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uid)
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    title: Mapped[str] = mapped_column(String(300), default="未命名项目")
    style_id: Mapped[str] = mapped_column(String(120), default="auto")  # profile id 或 "auto"
    prompt: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    assets: Mapped[list["Asset"]] = relationship(back_populates="project")
    jobs: Mapped[list["RenderJob"]] = relationship(back_populates="project")


class Asset(Base):
    __tablename__ = "assets"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    kind: Mapped[str] = mapped_column(String(20), default="video")  # video | image
    storage_key: Mapped[str] = mapped_column(String(400))
    filename: Mapped[str] = mapped_column(String(400), default="")
    duration_s: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    project: Mapped["Project"] = relationship(back_populates="assets")


class RenderJob(Base):
    __tablename__ = "render_jobs"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    # queued → planning → generating → rendering → done | failed
    status: Mapped[str] = mapped_column(String(20), default="queued")
    provider: Mapped[str] = mapped_column(String(20), default="mock")
    style_id: Mapped[str] = mapped_column(String(120), default="auto")
    target_duration: Mapped[float] = mapped_column(Float, default=16.0)
    budget_usd: Mapped[float] = mapped_column(Float, default=5.0)
    reserve_usd: Mapped[float] = mapped_column(Float, default=0.0)
    spent_usd: Mapped[float] = mapped_column(Float, default=0.0)
    edl_json: Mapped[str] = mapped_column(Text, default="")
    output_key: Mapped[str] = mapped_column(String(400), default="")
    duration_s: Mapped[float] = mapped_column(Float, default=0.0)
    error: Mapped[str] = mapped_column(Text, default="")
    progress: Mapped[str] = mapped_column(Text, default="")  # 最近一条进度
    subtitles: Mapped[bool] = mapped_column(default=False)   # 是否烧逐字字幕
    subtitle_lang: Mapped[str] = mapped_column(String(8), default="")
    music: Mapped[bool] = mapped_column(default=False)       # 是否自动配乐
    music_category: Mapped[str] = mapped_column(String(20), default="")  # 空=director决定
    video_model: Mapped[str] = mapped_column(String(40), default="")  # fal模型覆盖(空=风格默认)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    project: Mapped["Project"] = relationship(back_populates="jobs")


class GenerationRequest(Base):
    __tablename__ = "generation_requests"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uid)
    job_id: Mapped[str] = mapped_column(ForeignKey("render_jobs.id"))
    provider: Mapped[str] = mapped_column(String(20))
    model: Mapped[str] = mapped_column(String(120))
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    commercial_ok: Mapped[int] = mapped_column(Integer, default=1)
    prompt: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class CreditLedger(Base):
    __tablename__ = "credit_ledger"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uid)
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    job_id: Mapped[str] = mapped_column(String(32), default="")
    kind: Mapped[str] = mapped_column(String(20))   # topup | spend | settle
    amount_usd: Mapped[float] = mapped_column(Float)  # 有符号：topup>0, spend<0
    note: Mapped[str] = mapped_column(String(300), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
