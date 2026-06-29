"""FalProvider — fal.ai 接入（主生成接入层）。

fal 一套 API+计费覆盖 Seedance/Kling/FLUX/Veo/…。异步 queue：submit → 轮询 → 取结果 URL → 下载。
（生产用 webhook；Phase 1 CLI 用轮询。）

支持的 model（FAL_MODELS）：
  seedance-2.0-fast / seedance-2.0   —  文生视频(t2v)，直接 prompt→视频，便宜
  kling-hq                            —  高质量档：FLUX 文生图(参考帧) → Kling 2.1 Pro 图生视频(i2v)
每个模型 payload schema 不同，已对 2026-06 fal 文档核对。

⚠️ 需要 FAL_KEY 或 FAL_API_KEY。未在无 key 环境跑过 kling-hq 全链路——接 key 后 QA 跑通一次。
只用标准库 urllib，避免引依赖。
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import time
import urllib.request
import urllib.error
from pathlib import Path

from .base import GenerationProvider, GenSpec, GenResult

FAL_QUEUE = "https://queue.fal.run"
DUR_MIN, DUR_MAX = 4, 15      # Seedance 时长范围(秒)
KLING_DURS = ("5", "10")      # Kling i2v 只支持 5/10 秒

# endpoint
EP_SEEDANCE_FAST = "bytedance/seedance-2.0/fast/text-to-video"
EP_SEEDANCE = "bytedance/seedance-2.0/text-to-video"
EP_FLUX = "fal-ai/flux/schnell"
EP_FLUX_LORA = "fal-ai/flux-lora"        # FLUX + 身份 LoRA（同一张脸）
EP_KLING_I2V = "fal-ai/kling-video/v2.1/pro/image-to-video"
EP_KLING3_PRO = "fal-ai/kling-video/v3/pro/image-to-video"       # Kling 3.0 Pro i2v
EP_KLING3_STD = "fal-ai/kling-video/v3/standard/image-to-video"  # Kling 3.0 标准 i2v
EP_TOPAZ_VIDEO = "fal-ai/topaz/upscale/video"                    # 视频升采样（→4K）

FAL_MODELS = {
    "seedance-2.0-fast": {"kind": "t2v", "endpoint": EP_SEEDANCE_FAST,
                          "usd_per_s": 0.05, "commercial_ok": True},
    "seedance-2.0":      {"kind": "t2v", "endpoint": EP_SEEDANCE,
                          "usd_per_s": 0.30, "commercial_ok": True},
    # 高质量档：FLUX 出参考帧 → Kling 2.1 Pro 动起来
    "kling-hq":          {"kind": "t2i_i2v", "t2i": EP_FLUX, "i2v": EP_KLING_I2V,
                          "usd_image": 0.003, "usd_i2v_5s": 0.45, "commercial_ok": True},
    # 用户照片直接动起来（图生视频）：一张照片 + 场景描述 → 视频
    "kling-i2v":         {"kind": "i2v", "endpoint": EP_KLING_I2V,
                          "usd_i2v_5s": 0.45, "commercial_ok": True},
    # Seedance 2.0 图生视频（真 i2v，吃关键帧）：480p/720p/1080p（4K 走 Topaz 升采样）
    "seedance-2.0-i2v":  {"kind": "i2v_seedance",
                          "endpoint": "bytedance/seedance-2.0/image-to-video",
                          "usd_per_s": 0.30, "commercial_ok": True},
    # Kling 3.0 Pro 图生视频：电影感 + 流畅运动（aspect 由首帧决定，无分辨率参数）
    "kling-3-pro":       {"kind": "i2v_kling3", "endpoint": EP_KLING3_PRO,
                          "usd_per_s": 0.112, "commercial_ok": True},
    "kling-3-std":       {"kind": "i2v_kling3", "endpoint": EP_KLING3_STD,
                          "usd_per_s": 0.084, "commercial_ok": True},
}


def _aspect_ratio(w: int, h: int) -> str:
    r = w / h
    table = {"9:16": 9/16, "3:4": 3/4, "1:1": 1.0, "4:3": 4/3, "16:9": 16/9, "21:9": 21/9}
    return min(table, key=lambda k: abs(table[k] - r))


class FalProvider(GenerationProvider):
    name = "fal"

    def __init__(self):
        self.key = (os.environ.get("FAL_KEY") or os.environ.get("FAL_API_KEY") or "").strip()
        self.resolution = os.environ.get("FAL_RESOLUTION", "720p")
        self.gen_audio = os.environ.get("FAL_GENERATE_AUDIO", "false").lower() == "true"

    def _require_key(self):
        if not self.key:
            raise RuntimeError(
                "FalProvider 需要 FAL_KEY 或 FAL_API_KEY（未设置）。"
                " export 后重试，或用 --provider mock 跑离线 spine。")

    @staticmethod
    def _clamp_dur(seconds: float) -> int:
        return max(DUR_MIN, min(DUR_MAX, int(round(seconds))))

    def estimate_cost(self, spec: GenSpec) -> float:
        m = FAL_MODELS.get(spec.model)
        if not m:
            return 0.0
        if m["kind"] in ("t2v", "i2v_seedance", "i2v_kling3"):
            return round(m["usd_per_s"] * self._clamp_dur(spec.duration_s), 4)
        if m["kind"] == "t2i_i2v":
            return round(m["usd_image"] + m["usd_i2v_5s"], 4)  # 5s 档
        if m["kind"] == "i2v":
            return round(m["usd_i2v_5s"], 4)
        return 0.0

    # ── HTTP ─────────────────────────────────────────────
    def _post(self, url: str, payload: dict) -> dict:
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                     headers={"Authorization": f"Key {self.key}",
                                              "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())

    def _get(self, url: str) -> dict:
        req = urllib.request.Request(url, headers={"Authorization": f"Key {self.key}"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())

    def _run(self, endpoint: str, payload: dict) -> dict:
        """提交一个 fal job 并轮询到完成，返回结果 json。"""
        submit = self._post(f"{FAL_QUEUE}/{endpoint}", payload)
        req_id = submit.get("request_id")
        status_url = submit.get("status_url") or f"{FAL_QUEUE}/{endpoint}/requests/{req_id}/status"
        result_url = submit.get("response_url") or f"{FAL_QUEUE}/{endpoint}/requests/{req_id}"
        for _ in range(150):  # 最多 ~12.5 分钟（Kling i2v 约 5 分钟）
            st = self._get(status_url)
            s = st.get("status")
            if s == "COMPLETED":
                break
            if s in ("FAILED", "ERROR"):
                raise RuntimeError(f"fal 失败 {endpoint}: {st}")
            time.sleep(5)
        else:
            raise TimeoutError(f"fal 超时 {endpoint}: {req_id}")
        return self._get(result_url)

    # ── 各能力 ───────────────────────────────────────────
    def _flux_t2i(self, prompt: str, w: int, h: int) -> str:
        res = self._run(EP_FLUX, {"prompt": prompt, "image_size": {"width": w, "height": h},
                                  "num_inference_steps": 4, "num_images": 1})
        return res["images"][0]["url"]

    def _flux_lora_t2i(self, prompt: str, lora_url: str, trigger: str | None, w: int, h: int) -> str:
        """FLUX + 身份 LoRA：生成同一张脸的参考帧。"""
        full = f"{trigger}, {prompt}" if trigger else prompt
        res = self._run(EP_FLUX_LORA, {
            "prompt": full, "image_size": {"width": w, "height": h},
            "num_inference_steps": 28, "num_images": 1,
            "loras": [{"path": lora_url, "scale": 1.0}],
        })
        return res["images"][0]["url"]

    def _kling_i2v(self, prompt: str, image_url: str, w: int, h: int) -> str:
        res = self._run(EP_KLING_I2V, {"prompt": prompt, "image_url": image_url,
                                       "duration": "5", "aspect_ratio": _aspect_ratio(w, h),
                                       "cfg_scale": 0.5})
        return res["video"]["url"]

    def _seedance_t2v(self, endpoint: str, prompt: str, dur_int: int, w: int, h: int) -> str:
        payload = {"prompt": prompt, "duration": str(dur_int), "resolution": self.resolution,
                   "aspect_ratio": _aspect_ratio(w, h), "generate_audio": self.gen_audio}
        res = self._run(endpoint, payload)
        return (res.get("video") or {}).get("url") or res.get("url")

    def _kling3_i2v(self, endpoint: str, prompt: str, image_uri: str, dur_int: int) -> str:
        """Kling 3.0 图生视频：吃首帧（start_image_url），aspect 由首帧决定，无分辨率参数。"""
        payload = {"start_image_url": image_uri, "prompt": prompt,
                   "duration": str(dur_int), "generate_audio": self.gen_audio}
        res = self._run(endpoint, payload)
        return (res.get("video") or {}).get("url") or res.get("url")

    def topaz_upscale_video(self, video_url: str) -> str:
        """视频升采样（1080p → 4K）。输入可为 http(s) URL 或本地路径（自动上传）。"""
        if not str(video_url).startswith("http"):
            import fal_client
            video_url = fal_client.upload_file(str(video_url))
        res = self._run(EP_TOPAZ_VIDEO, {"video_url": video_url})
        return (res.get("video") or {}).get("url") or res.get("url")

    def _seedance_i2v(self, endpoint: str, prompt: str, image_uri: str,
                      dur_int: int, w: int, h: int) -> str:
        """Seedance 2.0 图生视频：关键帧 + 运动描述 → 视频（吃首帧）。"""
        payload = {"prompt": prompt, "image_url": image_uri, "resolution": self.resolution,
                   "duration": str(dur_int), "aspect_ratio": _aspect_ratio(w, h),
                   "generate_audio": self.gen_audio}
        res = self._run(endpoint, payload)
        return (res.get("video") or {}).get("url") or res.get("url")

    def _image_data_uri(self, path: str) -> str:
        """本地照片 → 缩放(≤1024) + jpeg + base64 data URI（fal image_url 接受 data URI）。"""
        from .. import WORK_DIR
        tmp = WORK_DIR / "gen" / "seed.jpg"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", path,
                        "-vf", "scale='min(1024,iw)':-2", "-q:v", "4", str(tmp)], check=True)
        return "data:image/jpeg;base64," + base64.b64encode(tmp.read_bytes()).decode()

    def _download(self, url: str, name: str) -> str:
        from .. import WORK_DIR
        out_dir = WORK_DIR / "gen"
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / name
        urllib.request.urlretrieve(url, out)
        return str(out)

    # ── 统一入口 ─────────────────────────────────────────
    def submit(self, spec: GenSpec) -> GenResult:
        self._require_key()
        m = FAL_MODELS.get(spec.model)
        if not m:
            raise ValueError(f"未知 fal model: {spec.model}（可选: {list(FAL_MODELS)}）")
        w, h = spec.width, spec.height

        if m["kind"] == "t2v":
            dur_int = self._clamp_dur(spec.duration_s)
            video_url = self._seedance_t2v(m["endpoint"], spec.prompt, dur_int, w, h)
            dur_out = float(dur_int)
            ver = m["endpoint"]
            extra = {"resolution": self.resolution, "generate_audio": self.gen_audio}
        elif m["kind"] == "t2i_i2v":
            if spec.lora_url:                                    # 身份角色：FLUX+LoRA 出参考帧
                image_url = self._flux_lora_t2i(spec.prompt, spec.lora_url, spec.trigger_word, w, h)
            else:
                image_url = self._flux_t2i(spec.prompt, w, h)    # 普通参考帧
            video_url = self._kling_i2v(spec.prompt, image_url, w, h)  # 动起来(5s)
            dur_out = min(float(spec.duration_s), 5.0)            # 渲染时按计划裁
            ver = f"{'flux-lora' if spec.lora_url else m['t2i']}+{m['i2v']}"
            extra = {"reference_image": image_url}
        elif m["kind"] == "i2v":
            if not spec.image_path:
                raise ValueError("kling-i2v 需要 image_path（一张照片）")
            img_uri = self._image_data_uri(spec.image_path)      # 用户照片当首帧
            video_url = self._kling_i2v(spec.prompt, img_uri, w, h)
            dur_out = min(float(spec.duration_s), 5.0)
            ver = m["endpoint"]
            extra = {"seed_image": spec.image_path}
        elif m["kind"] == "i2v_seedance":
            if not spec.image_path:
                raise ValueError("seedance-2.0-i2v 需要 image_path（关键帧）")
            img_uri = self._image_data_uri(spec.image_path)
            dur_int = self._clamp_dur(spec.duration_s)
            video_url = self._seedance_i2v(m["endpoint"], spec.prompt, img_uri, dur_int, w, h)
            dur_out = float(dur_int)
            ver = m["endpoint"]
            extra = {"seed_image": spec.image_path, "resolution": self.resolution}
        elif m["kind"] == "i2v_kling3":
            if not spec.image_path:
                raise ValueError("kling-3 需要 image_path（关键帧）")
            img_uri = self._image_data_uri(spec.image_path)
            dur_int = self._clamp_dur(spec.duration_s)
            video_url = self._kling3_i2v(m["endpoint"], spec.prompt, img_uri, dur_int)
            dur_out = float(dur_int)
            ver = m["endpoint"]
            extra = {"seed_image": spec.image_path}
        else:
            raise ValueError(f"未知 kind: {m['kind']}")

        if not video_url:
            raise RuntimeError(f"fal 结果无 video url（model={spec.model}）")
        out = self._download(video_url, f"fal_{spec.model}_{abs(hash(video_url)) % 10**8}.mp4")
        return GenResult(local_path=out, provider=self.name, model=spec.model,
                         model_version=ver, cost_usd=self.estimate_cost(spec),
                         commercial_ok=m["commercial_ok"], duration_s=dur_out,
                         raw={"video_url": video_url, **extra})
