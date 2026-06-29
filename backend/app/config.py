"""配置与路径。Phase 1 dev 默认零依赖（SQLite + 本地磁盘）。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent          # open-edit/backend
PROJECT_ROOT = BACKEND_DIR.parent                              # open-edit
DATA_DIR = BACKEND_DIR / ".data"
STORAGE_DIR = DATA_DIR / "storage"
WORK_DIR = DATA_DIR / "work"
DB_PATH = DATA_DIR / "openedit.db"

for d in (DATA_DIR, STORAGE_DIR, WORK_DIR):
    d.mkdir(parents=True, exist_ok=True)

# 让 `engine` 可被 import（engine 与 backend 同在 open-edit/ 下）
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")
DEFAULT_PROVIDER = os.environ.get("OPENEDIT_PROVIDER", "mock")  # mock | fal
WORKER_CONCURRENCY = int(os.environ.get("OPENEDIT_WORKERS", "2"))
DEFAULT_JOB_BUDGET_USD = float(os.environ.get("OPENEDIT_JOB_BUDGET", "5.0"))
SEED_CREDITS_USD = float(os.environ.get("OPENEDIT_SEED_CREDITS", "20.0"))


def _load_fal_key_from_autoclip() -> None:
    """便利：若环境没有 FAL_API_KEY，尝试从 AutoClip/api/.env 读（Mr.Gao 的 key 在那）。"""
    if os.environ.get("FAL_API_KEY") or os.environ.get("FAL_KEY"):
        return
    env_file = PROJECT_ROOT.parent / "AutoClip" / "api" / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip().startswith("FAL_API_KEY="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    os.environ["FAL_API_KEY"] = val
                break


_load_fal_key_from_autoclip()
