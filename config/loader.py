"""config.loader — open-edit 统一密钥加载。

把 config/secrets.env 的 key 注入 os.environ，全项目单一来源。
fal provider 读 FAL_KEY/FAL_API_KEY；这里把 FAL_API_KEY 也映射到 FAL_KEY。

用法：
    from config.loader import load_keys
    load_keys()
"""
from __future__ import annotations

import os
from pathlib import Path

SECRETS = Path(__file__).resolve().parent / "secrets.env"

# 同义映射：有些库读不同变量名
_ALIASES = {
    "FAL_API_KEY": ["FAL_KEY"],
}


def load_keys(path: Path | None = None, override: bool = False) -> list[str]:
    """加载 secrets.env → os.environ，返回加载到的 key 名列表（不含值）。"""
    p = path or SECRETS
    if not p.exists():
        return []
    loaded = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):       # 兼容 ~/.zshrc 风格
            line = line[len("export "):]
        k, _, v = line.partition("=")
        k, v = k.strip(), v.split("#", 1)[0].strip().strip('"').strip("'")
        if not v:
            continue
        if override or not os.environ.get(k):
            os.environ[k] = v
        loaded.append(k)
        for alias in _ALIASES.get(k, []):
            if override or not os.environ.get(alias):
                os.environ[alias] = v
    return loaded


if __name__ == "__main__":
    keys = load_keys()
    print(f"已加载 {len(keys)} 个密钥：{sorted(set(keys))}" if keys
          else "secrets.env 不存在或为空（先从 api_keys.example.env 复制并填值）")
