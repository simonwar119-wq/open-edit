#!/usr/bin/env python3
"""character — 身份一致角色资产（多角度照片 → FLUX LoRA 身份模型）。

训一次脸 → 得到一个可复用的 character 资产 {name, trigger_word, lora_url}，
之后 AI 导演生成镜头时用 FLUX+LoRA 保持同一张脸（再 Kling 动起来）。

  train_character(name, photos)  多角度照片 → 打包上传 fal → flux-lora 训练 → 存档
  load_character / list_characters

训练用 fal（约 $2/次，5–10 分钟）。需 FAL_KEY/FAL_API_KEY。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import zipfile
from pathlib import Path

from . import ENGINE_DIR, WORK_DIR

CHARACTERS_DIR = ENGINE_DIR / "characters"


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9_-]+", "-", name.lower().strip()).strip("-")
    if s:
        return s
    # 纯中文/非 ASCII 名 → 用名字 hash 生成稳定且唯一的 slug（避免都塌成 "char" 互相覆盖）
    return "c-" + hashlib.sha1(name.strip().encode("utf-8")).hexdigest()[:8]


def _ensure_key():
    if not (os.environ.get("FAL_KEY") or os.environ.get("FAL_API_KEY")):
        raise RuntimeError("训练需要 FAL_KEY 或 FAL_API_KEY")
    # fal_client 读 FAL_KEY
    if not os.environ.get("FAL_KEY") and os.environ.get("FAL_API_KEY"):
        os.environ["FAL_KEY"] = os.environ["FAL_API_KEY"]


def train_character(name: str, photo_paths: list[str], trigger_word: str | None = None,
                    steps: int = 1000, log=lambda m: None) -> dict:
    """多角度照片 → 训练 FLUX LoRA 身份模型 → 存 character 资产。"""
    _ensure_key()
    import fal_client

    photos = [p for p in photo_paths if Path(p).exists()]
    if len(photos) < 4:
        raise ValueError(f"至少 4 张照片（建议 10–20 张多角度/多表情），当前 {len(photos)}")
    trigger = trigger_word or f"{_slug(name)}_person"

    zpath = WORK_DIR / f"char_{_slug(name)}.zip"
    with zipfile.ZipFile(zpath, "w") as z:
        for i, p in enumerate(photos):
            z.write(p, f"{i:03d}{Path(p).suffix.lower()}")
    log(f"打包 {len(photos)} 张照片并上传 fal …")
    images_url = fal_client.upload_file(str(zpath))

    log(f"训练 LoRA（trigger='{trigger}', steps={steps}, 约 $2, 5–10 分钟）…")
    result = fal_client.subscribe(
        "fal-ai/flux-lora-fast-training",
        arguments={"images_data_url": images_url, "trigger_word": trigger, "steps": steps},
        with_logs=False,
    )
    lora_url = ((result.get("diffusers_lora_file") or {}).get("url")
                or (result.get("lora_file") or {}).get("url") or result.get("lora_url"))
    if not lora_url:
        raise RuntimeError(f"训练完成但未拿到 lora url: {list(result)}")

    CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)
    prof = {"name": name, "slug": _slug(name), "trigger_word": trigger,
            "lora_url": lora_url, "steps": steps, "n_photos": len(photos)}
    (CHARACTERS_DIR / f"{_slug(name)}.json").write_text(
        json.dumps(prof, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"角色资产已存：{_slug(name)}.json")
    return prof


def load_character(name: str) -> dict:
    p = CHARACTERS_DIR / f"{_slug(name)}.json"
    if not p.exists():
        avail = [f.stem for f in CHARACTERS_DIR.glob("*.json")] if CHARACTERS_DIR.exists() else []
        raise FileNotFoundError(f"找不到角色: {name}（可用: {avail}）")
    return json.loads(p.read_text(encoding="utf-8"))


def list_characters() -> list[dict]:
    if not CHARACTERS_DIR.exists():
        return []
    out = []
    for f in sorted(CHARACTERS_DIR.glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            out.append({"name": d.get("name"), "slug": d.get("slug", f.stem),
                        "trigger_word": d.get("trigger_word"), "n_photos": d.get("n_photos"),
                        "trained": bool(d.get("lora_url"))})
        except Exception:
            continue
    return out
