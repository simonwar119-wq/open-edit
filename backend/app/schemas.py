"""Pydantic 请求/响应模型（OpenAPI 即由此生成 → iOS/web 自动生成 client）。"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class MeOut(BaseModel):
    org_id: str
    email: str
    balance_usd: float


class TopupIn(BaseModel):
    amount_usd: float


class ProjectCreate(BaseModel):
    title: str = "未命名项目"
    style_id: str = "auto"          # profile id/file 或 "auto"（让编排层选）
    prompt: str = ""


class ProjectOut(BaseModel):
    id: str
    title: str
    style_id: str
    prompt: str

    class Config:
        from_attributes = True


class AssetOut(BaseModel):
    id: str
    kind: str
    filename: str
    duration_s: float

    class Config:
        from_attributes = True


class RenderCreate(BaseModel):
    target_duration: float = 16.0
    provider: str = "mock"          # mock | fal
    budget_usd: float = 5.0
    style_id: Optional[str] = None  # 覆盖项目风格；None=用项目的
    subtitles: bool = False         # 是否烧逐字字幕（Whisper）
    subtitle_lang: Optional[str] = None  # zh/en…，None=自动
    music: bool = False             # 是否自动配乐
    music_category: Optional[str] = None  # tech|warm|energetic|cinematic，None=director决定
    video_model: Optional[str] = None  # seedance-2.0-fast|seedance-2.0|kling-hq，None=风格默认


class JobOut(BaseModel):
    id: str
    status: str
    provider: str
    style_id: str
    target_duration: float
    reserve_usd: float
    spent_usd: float
    duration_s: float
    progress: str
    error: str
    output_url: Optional[str] = None
    edl_summary: Optional[dict] = None
    director: Optional[dict] = None     # AI 导演决策：风格/理由/创作指令/来源/素材特征


class StyleOut(BaseModel):
    id: str
    file: str
    display_name: str
    inspiration: str
    asl_seconds: Optional[float] = None
    named_look: Optional[str] = None
