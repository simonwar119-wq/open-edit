"""GenerationProvider 统一接口 + 数据契约。

每个生成厂商实现 submit(spec) -> result。result 必须带 cost_usd 与 commercial_ok，
因为 SaaS 要转售生成内容（plan 的法律红线）+ 按生成秒数计费。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class GenSpec:
    """一次生成请求的规格（一个镜头）。"""
    prompt: str
    kind: str = "t2v"          # t2v | i2v | talkinghead
    duration_s: float = 4.0
    width: int = 720
    height: int = 1280
    fps: int = 24
    model: str = "mock"
    image_path: Optional[str] = None   # i2v 的输入图
    seed: Optional[int] = None
    lora_url: Optional[str] = None      # 身份角色 LoRA（FLUX+LoRA 生成同一张脸）
    trigger_word: Optional[str] = None  # LoRA 触发词

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GenResult:
    """一次生成的结果 + 计费/合规元数据。"""
    local_path: str            # 落地的 clip 文件（Phase 0 本地；Phase 1 → R2 key）
    provider: str
    model: str
    cost_usd: float
    commercial_ok: bool
    duration_s: float
    model_version: str = ""
    raw: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class GenerationProvider(ABC):
    """所有生成厂商的基类。"""

    name: str = "base"

    @abstractmethod
    def submit(self, spec: GenSpec) -> GenResult:
        """同步产出一个 clip（内部可异步轮询/webhook，对外阻塞返回）。"""
        raise NotImplementedError

    def estimate_cost(self, spec: GenSpec) -> float:
        """烧钱前的预估（reserve 用）。子类按 model 单价×秒数覆盖。"""
        return 0.0
