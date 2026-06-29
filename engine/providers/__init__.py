"""生成 provider 接入层。

所有厂商（fal.ai / PiAPI / HeyGen / ElevenLabs / Mock）收口到统一接口
`GenerationProvider`，持久化 provider+model+version+cost+commercial_ok。
Phase 0 只实现 MockProvider（离线、零成本）与 FalProvider（需 FAL_KEY）。
"""

from .base import GenerationProvider, GenSpec, GenResult
from .mock import MockProvider


def get_provider(name: str) -> GenerationProvider:
    """按名字取 provider 实例。"""
    name = (name or "mock").lower()
    if name == "mock":
        return MockProvider()
    if name == "fal":
        from .fal import FalProvider  # 延迟导入，避免无 key 时报错
        return FalProvider()
    raise ValueError(f"未知 provider: {name}（可选: mock | fal）")


__all__ = ["GenerationProvider", "GenSpec", "GenResult", "MockProvider", "get_provider"]
