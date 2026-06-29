"""LLM 客户端抽象 —— 「AI 导演」的大脑。

Claude 优先（plan 定调），可插拔到 OpenAI 兼容（DeepSeek/豆包，Mr.Gao 现有栈）。
通过环境变量启用，缺 key 时 orchestrator 自动回退到启发式（系统仍可跑）。

启用真 LLM（二选一）：
  # A. Claude（默认）
  export OPENEDIT_LLM_PROVIDER=anthropic
  export OPENEDIT_LLM_API_KEY=sk-ant-...           # 或设 ANTHROPIC_API_KEY
  export OPENEDIT_LLM_MODEL=claude-sonnet-4-6      # 可选
  # B. DeepSeek（OpenAI 兼容，便宜，你 AutoClip 已有）
  export OPENEDIT_LLM_PROVIDER=openai
  export OPENEDIT_LLM_API_KEY=sk-...
  export OPENEDIT_LLM_BASE_URL=https://api.deepseek.com
  export OPENEDIT_LLM_MODEL=deepseek-chat
  # C. 离线自测
  export OPENEDIT_LLM_PROVIDER=mock
"""

from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod

import httpx


class LLMClient(ABC):
    name = "base"

    @abstractmethod
    def complete_json(self, system: str, user: str) -> dict: ...


def _extract_json(text: str) -> dict:
    """从模型输出里抠出 JSON（容忍 ```json 包裹 / 前后废话）。"""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    else:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            text = m.group(0)
    return json.loads(text)


class AnthropicClient(LLMClient):
    name = "anthropic"

    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def complete_json(self, system: str, user: str) -> dict:
        r = httpx.post(
            f"{self.base_url}/v1/messages",
            headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": self.model, "max_tokens": 1024, "system": system,
                  "messages": [{"role": "user", "content": user}]},
            timeout=60,
        )
        r.raise_for_status()
        text = "".join(b.get("text", "") for b in r.json().get("content", []))
        return _extract_json(text)


class OpenAICompatClient(LLMClient):
    name = "openai-compat"

    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def complete_json(self, system: str, user: str) -> dict:
        r = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}",
                     "content-type": "application/json"},
            json={"model": self.model,
                  "messages": [{"role": "system", "content": system},
                               {"role": "user", "content": user}],
                  "response_format": {"type": "json_object"}, "temperature": 0.4},
            timeout=60,
        )
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
        return _extract_json(text)


class MockLLMClient(LLMClient):
    """离线自测：用 footage 特征 + prompt 关键词做一个"像 LLM"的结构化决策。"""
    name = "mock"

    def complete_json(self, system: str, user: str) -> dict:
        # 只看「创作意图」「目标时长」「素材」，别被风格库描述文本干扰（真 LLM 不会被干扰）
        intent, target, n_assets, forced = user.lower(), 14.0, 0, None
        try:
            d = json.loads(user)
            intent = str(d.get("创作意图", "")).lower()
            target = float(d.get("目标时长秒", 14) or 14)
            n_assets = (d.get("素材画面特征", {}) or {}).get("aggregate", {}).get("count", 0) or 0
            fs = d.get("指定风格", "")
            forced = fs if fs and "未指定" not in str(fs) else None
        except Exception:
            pass

        warm = any(k in intent for k in ["暖", "粉", "甜", "对称", "可爱", "下午茶", "马卡龙", "明亮", "pastel"])
        cold = any(k in intent for k in ["冷", "暗", "夜", "悬疑", "高级", "克制", "厚重", "noir"])
        if forced:
            style = forced
            directives = "按指定风格统一光线与色调"
        elif warm and not cold:
            style, directives = "wes-anderson-inspired", "对称居中构图，粉彩高调，平正正面光，明快"
        else:
            style, directives = "fincher-inspired", "低照度、克制运镜、冷调去饱和、厚重质感"

        # 拆 shot-plan：镜头数≈目标/4，upload/generate 交替，首镜 cut，中段一个 dissolve
        n = max(3, min(8, round(target / 4)))
        per = round(target / n, 1)
        scales = ["WS", "MS", "CU"]
        shots = []
        for i in range(n):
            role = "hook" if i == 0 else ("close" if i == n - 1 else ("climax" if i >= n - 2 else "body"))
            source = "upload" if (n_assets > 0 and i % 2 == 0) else "generate"
            shots.append({
                "role": role, "source": source, "duration_s": per,
                "shot_scale": scales[i % 3],
                "prompt": f"{intent}（{role} 镜头，{scales[i % 3]}）" if source == "generate" else "",
                "transition_in": {"type": "dissolve", "duration": 0.5} if i == n // 2 else {"type": "cut", "duration": 0.0},
            })
        music_cat = "warm" if style == "wes-anderson-inspired" else "cinematic"
        return {"style_file": style, "reason": f"意图/素材判定 → {style}（mock 排了 {n} 个镜头）",
                "creative_directives": directives, "shots": shots, "music_category": music_cat}


def get_llm() -> LLMClient | None:
    """按 env 造 LLM；缺 provider/key → None（orchestrator 回退启发式）。"""
    provider = os.environ.get("OPENEDIT_LLM_PROVIDER", "").lower().strip()
    key = os.environ.get("OPENEDIT_LLM_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")
    model = os.environ.get("OPENEDIT_LLM_MODEL", "")

    if provider == "mock":
        return MockLLMClient()
    if not provider:
        provider = "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else ""
    if not provider or not key:
        return None
    if provider == "anthropic":
        base = os.environ.get("OPENEDIT_LLM_BASE_URL") or os.environ.get(
            "ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        return AnthropicClient(key, model or "claude-sonnet-4-6", base)
    if provider in ("openai", "openai-compat", "deepseek"):
        base = os.environ.get("OPENEDIT_LLM_BASE_URL", "https://api.openai.com/v1")
        return OpenAICompatClient(key, model or "gpt-4o-mini", base)
    return None
