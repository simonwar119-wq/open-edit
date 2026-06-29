"""Open Edit v2 — engine 内核（Phase 0 CLI 纵切）

生成即核心的 AI 电影短片流水线的 Python 内核：
    build_edl.py  : prompt + 风格 → 反向分镜 → 调生成 provider → 产出 EDL(JSON)
    render.py     : EDL(JSON) → FFmpeg(剪辑+转场+CDL/LUT 调色) → MP4
内核之后由 backend/(FastAPI+Temporal) 包成服务。
"""

from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ENGINE_DIR.parent
PROFILES_DIR = ENGINE_DIR / "profiles"
LUTS_DIR = ENGINE_DIR / "luts"
WORK_DIR = ENGINE_DIR / ".work"  # 中间产物（normalized clips 等）

__all__ = ["ENGINE_DIR", "PROJECT_ROOT", "PROFILES_DIR", "LUTS_DIR", "WORK_DIR"]
