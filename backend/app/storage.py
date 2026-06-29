"""存储抽象。Phase 1 = 本地磁盘；生产 = Cloudflare R2（同一接口）。"""

from __future__ import annotations

import shutil
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from .config import STORAGE_DIR


class Storage(ABC):
    @abstractmethod
    def put(self, local_path: str, key: str | None = None) -> str: ...
    @abstractmethod
    def local_path(self, key: str) -> Path: ...


class LocalStorage(Storage):
    """落地到 backend/.data/storage/<key>。key 形如 'assets/<uuid>.mp4'。"""

    def __init__(self, root: Path = STORAGE_DIR):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, local_path: str, key: str | None = None) -> str:
        src = Path(local_path)
        key = key or f"misc/{uuid.uuid4().hex}{src.suffix}"
        dst = self.root / key
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.resolve() != dst.resolve():
            shutil.copy2(src, dst)
        return key

    def local_path(self, key: str) -> Path:
        return self.root / key


# 生产替换：class R2Storage(Storage) —— boto3/S3 兼容，put 走 multipart，local_path 改 presigned URL。

storage: Storage = LocalStorage()
