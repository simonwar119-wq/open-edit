#!/usr/bin/env python3
"""open-edit webui — 本地操作网页（参考 Higgsfield 生成界面）。

三个 tab（对应设计文档三大功能）：
  出片  ：上传脸/选角色 → 场景关键帧 → 相机+运动 → i2v 出片
  换场景：上传一段视频 → 一句话换场景/背景（保留原音）→ Kling O1 编辑
  换脸  ：（2B，最复杂，待验证）即将上线

引擎全复用 engine.*。启动：backend/.venv/bin/python webui/app.py（http://127.0.0.1:5050）
"""
from __future__ import annotations

import sys, os, time, json, hashlib, subprocess, base64, urllib.request, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from flask import Flask, request, jsonify, send_file, Response  # noqa: E402
from config.loader import load_keys  # noqa: E402
from engine.character import load_character, list_characters  # noqa: E402
from engine.prompt_kit import mcsla, realism_suffix  # noqa: E402
from engine.providers import get_provider  # noqa: E402
from engine.providers.base import GenSpec  # noqa: E402
from engine import seedance_lint, ledger  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent / "outputs"
REF_DIR = OUT_DIR / "refs"
for d in (OUT_DIR, REF_DIR):
    d.mkdir(parents=True, exist_ok=True)
PRESETS_PATH = ROOT / "taxonomy" / "dop_camera_presets.json"
LEDGER_PROJECT = "webui"

ASPECTS = {
    "9:16": {"kf": (768, 1344), "vid": (720, 1280), "label": "竖屏 9:16"},
    "16:9": {"kf": (1344, 768), "vid": (1280, 720), "label": "横屏 16:9"},
    "1:1":  {"kf": (1024, 1024), "vid": (1024, 1024), "label": "方形 1:1"},
}
# 出片(i2v)模型 —— usd 用于前端估算；res_native=是否吃分辨率参数(Kling 由关键帧决定，不吃)
VID_MODELS = [
    {"value": "mock",             "label": "占位（免费）",          "per_s": 0.0,   "flat5": None, "res_native": True},
    {"value": "seedance-2.0-i2v", "label": "Seedance 2.0",         "per_s": 0.30,  "flat5": None, "res_native": True},
    {"value": "kling-3-pro",      "label": "Kling 3.0 Pro（电影感）", "per_s": 0.112, "flat5": None, "res_native": False},
    {"value": "kling-3-std",      "label": "Kling 3.0 标准（便宜）",  "per_s": 0.084, "flat5": None, "res_native": False},
]
RESOLUTIONS = ["480p", "720p", "1080p", "4K"]
RES_DEFAULT = "720p"
TOPAZ_USD_PER_S = 0.08  # 4K 升采样
DURATIONS = [4, 5, 8, 10]
DUR_DEFAULT = 5

# 换场景(2A) v2v 编辑模型 —— endpoint=None 为占位；validated=已在本项目实测；max_s/min_s=输入时长约束
RESTYLE_MODELS = [
    {"value": "mock",     "label": "占位（免费）",              "endpoint": None,
     "per_s": 0.0,   "keep_audio": True,  "validated": True,  "min_s": 0,  "max_s": None},
    {"value": "kling-o1", "label": "Kling O1 编辑（保原音·已验证）", "endpoint": "fal-ai/kling-video/o1/video-to-video/edit",
     "per_s": 0.168, "keep_audio": True,  "validated": True,  "min_s": 3,  "max_s": 10},
    {"value": "wan-v2v",  "label": "Wan 2.2 v2v（实验）",        "endpoint": "fal-ai/wan/v2.2-a14b/video-to-video",
     "per_s": 0.10,  "keep_audio": False, "validated": False, "min_s": 0,  "max_s": 5},
    {"value": "luma-modify", "label": "Luma Ray2 Modify（实验）", "endpoint": "fal-ai/luma-dream-machine/ray-2/modify",
     "per_s": 0.12,  "keep_audio": False, "validated": False, "min_s": 0,  "max_s": 10},
]
# 换脸(2B) Kling Motion Control —— move=连背景一起换 / replace=只换人
REFACE_MODELS = [
    {"value": "mock",            "label": "占位（免费）",         "endpoint": None,
     "mode_param": None,      "per_s": 0.0,   "validated": True,  "min_s": 0, "max_s": None},
    {"value": "kling-replace",   "label": "Kling 换人·留背景（实验）", "endpoint": "fal-ai/kling-video/v1.6/pro/motion-control",
     "mode_param": "replace", "per_s": 0.168, "validated": False, "min_s": 3, "max_s": 10},
    {"value": "kling-move",      "label": "Kling 换人+换背景（实验）", "endpoint": "fal-ai/kling-video/v1.6/pro/motion-control",
     "mode_param": "move",    "per_s": 0.168, "validated": False, "min_s": 3, "max_s": 10},
]
RESTYLE_MAP = {m["value"]: m for m in RESTYLE_MODELS}
REFACE_MAP = {m["value"]: m for m in REFACE_MODELS}


def _dims(aspect):
    a = ASPECTS.get(aspect, ASPECTS["9:16"])
    return a["kf"], a["vid"]


def _key():
    return os.environ.get("FAL_KEY") or os.environ["FAL_API_KEY"]


def _post(u, b):
    return json.loads(urllib.request.urlopen(urllib.request.Request(
        u, data=json.dumps(b).encode(), method="POST",
        headers={"Authorization": f"Key {_key()}", "Content-Type": "application/json"}), timeout=90).read())


def _get(u):
    return json.loads(urllib.request.urlopen(urllib.request.Request(
        u, headers={"Authorization": f"Key {_key()}"}), timeout=90).read())


def _poll(endpoint_sub):
    su, ru = endpoint_sub["status_url"], endpoint_sub["response_url"]
    for _ in range(180):
        st = _get(su)
        if st.get("status") == "COMPLETED":
            return _get(ru)
        if st.get("status") in ("FAILED", "ERROR"):
            raise RuntimeError(f"fal 失败: {st}")
        time.sleep(5)
    raise TimeoutError("fal 超时")


LOADED_KEYS = load_keys()
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 60 * 1024 * 1024


def _camera_presets():
    data = json.loads(PRESETS_PATH.read_text(encoding="utf-8"))
    return [{"name": p["name"], "best_for": p.get("best_for", ""),
             "fragment": p.get("prompt_fragment", "")} for p in data["presets"]]


def _camera_lookup(name):
    if not name:
        return None
    for p in json.loads(PRESETS_PATH.read_text(encoding="utf-8"))["presets"]:
        if p["name"] == name:
            return p
    return None


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _data_uri(path, maxpx=1024):
    tmp = REF_DIR / "_u.jpg"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(path),
                    "-vf", f"scale='min({maxpx},iw)':-2", "-q:v", "3", str(tmp)], check=True)
    return "data:image/jpeg;base64," + base64.b64encode(tmp.read_bytes()).decode()


def _vid_dur(path):
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip()
        return float(out)
    except Exception:
        return 5.0


def _kf_prompt(scene, cam, subject):
    return mcsla(subject=subject, action="present in the scene", look=scene, camera=cam or None)


# ── DeepSeek 提示词扩写（写死规则：把大白话扩成模型能精准识别的详细指令）─────────
def _deepseek(system, user):
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("缺少 DEEPSEEK_API_KEY")
    base = (os.environ.get("DEEPSEEK_BASE_URL") or "https://api.deepseek.com").rstrip("/")
    model = os.environ.get("DEEPSEEK_MODEL") or "deepseek-chat"
    body = {"model": model, "temperature": 0.7, "max_tokens": 700, "stream": False,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    req = urllib.request.Request(base + "/chat/completions", data=json.dumps(body).encode(),
                                 method="POST", headers={"Authorization": f"Bearer {key}",
                                                         "Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=90).read())
    return r["choices"][0]["message"]["content"].strip()


_RULE = ("你是顶级 AI 视频/图像提示词工程师。把用户用大白话填的内容，自动扩写成"
         "“详细到细节”的生成指令，让下游生成模型能完美读取识别、不产生歧义。"
         "只输出最终提示词本身，不要解释、不要标题、不要引号、不要列表符号。"
         "真实感用词：visible skin pores, raw photo, natural light, 35mm film grain；"
         "严禁塑料触发词：flawless, perfect skin, 8K, hyper-detailed, CGI。")
ENHANCE_SYSTEM = {
    # 出片·关键帧场景（喂图像模型 NBP/FLUX）
    "scene": _RULE + " 目标=图像关键帧。输出英文，≤120 词，写清：主体与姿态、所处环境与背景细节、"
             "光线（方向/质感/色温）、镜头与构图（景别/焦段/景深）、色调与氛围。"
             "用 the person/the character 指代人物身份，不要替换成具体名人。",
    # 出片·运动（喂 i2v Seedance/Kling）—— 必须围绕指定运镜来写
    "motion": _RULE + " 目标=图生视频的运动描述。输出英文，≤70 词。"
              "若用户给了指定运镜（camera move），**整段动作必须围绕这一个运镜来组织**，"
              "把该运镜作为本镜唯一的主导镜头运动，自然融入英文描述（不要再加第二个运镜）。"
              "写清：人物/主体在这个运镜下做什么动作。不要重复描述场景（关键帧已定）。"
              "避免直接写 slow-motion 液体（易崩），如需慢感用正常速描述。",
    # 换场景·v2v 编辑（喂 Kling O1 Edit）
    "restyle": _RULE + " 目标=视频换场景/背景编辑指令。输出英文，≤100 词，写清新场景的具体视觉细节"
               "（材质/灯光/陈设/色调），并明确指令：keep the person, their motion, the camera movement "
               "and framing exactly unchanged。Photorealistic。",
    # 换脸·目标描述
    "reface": _RULE + " 目标=换脸/换人的目标描述。输出英文，≤80 词，写清目标人物的外貌身份细节"
              "（性别/年龄段/发型/着装/神态）与（可选）目标场景。",
}


def _nbp_keyframe(prompt, ref_path, aspect):
    uri = _data_uri(ref_path)
    full = "THIS exact person (keep their face and identity identical to the reference photo). " + prompt
    res = _poll(_post("https://queue.fal.run/fal-ai/nano-banana-pro/edit",
                      {"prompt": full, "image_urls": [uri], "num_images": 1,
                       "aspect_ratio": aspect, "output_format": "jpeg"}))
    return res["images"][0]["url"]


def _v2v_edit(endpoint, video_path, prompt, keep_audio, supports_audio):
    """通用 video-to-video 编辑：上传视频 → 提交端点 → 轮询取结果。"""
    import fal_client
    video_url = fal_client.upload_file(str(video_path))
    payload = {"video_url": video_url, "prompt": prompt}
    if supports_audio:
        payload["keep_audio"] = bool(keep_audio)
    res = _poll(_post(f"https://queue.fal.run/{endpoint}", payload))
    return (res.get("video") or {}).get("url") or res.get("url")


def _motion_control(endpoint, video_path, first_frame_url, mode_param):
    """换脸(2B)：参考视频 + 改好的首帧 → Kling Motion Control。端点接入需核对。"""
    import fal_client
    video_url = fal_client.upload_file(str(video_path))
    payload = {"video_url": video_url, "image_url": first_frame_url}
    if mode_param:
        payload["mode"] = mode_param
    res = _poll(_post(f"https://queue.fal.run/{endpoint}", payload))
    return (res.get("video") or {}).get("url") or res.get("url")


def _first_frame(video_path):
    out = REF_DIR / ("ff_" + hashlib.sha1(str(video_path).encode()).hexdigest()[:12] + ".jpg")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(video_path),
                    "-vframes", "1", str(out)], check=True)
    return out


def _trim_video(video_path, seconds):
    """截取前 N 秒（重编码，确保关键帧对齐）。返回新文件路径。"""
    out = REF_DIR / ("trim_" + hashlib.sha1((str(video_path) + str(seconds)).encode()).hexdigest()[:12] + ".mp4")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(video_path),
                    "-t", str(seconds), "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", str(out)],
                   check=True)
    return out


def _enforce_dur(vp, m, trim):
    """按模型 min_s/max_s 校验输入视频时长。超长则按 trim 决定截取或报错。
    返回 (使用的视频路径, 计费时长秒, 错误消息或None)。"""
    dur = _vid_dur(vp)
    min_s, max_s = m.get("min_s", 0), m.get("max_s")
    if min_s and dur < min_s:
        return vp, dur, f"该模型要求输入 ≥{min_s} 秒，你的视频只有 {round(dur,1)} 秒"
    if max_s and dur > max_s + 0.2:
        if not trim:
            return vp, dur, (f"该模型输入上限 {max_s} 秒，你的视频 {round(dur,1)} 秒。"
                             f"勾选「超长自动截取前 {max_s} 秒」后重试，或先自己裁剪。")
        return _trim_video(vp, max_s), float(max_s), None
    return vp, dur, None


def _mock_keyframe(prompt, tag, w, h):
    key = hashlib.sha1((prompt + (tag or "") + f"{w}x{h}").encode()).hexdigest()[:12]
    out = OUT_DIR / f"keyframe_{key}.png"
    if out.exists():
        return out
    safe = ("MOCK | " + (tag or "") + " " + prompt)[:48]
    safe = safe.replace("\\", "").replace(":", " ").replace("'", "").replace("%", "").replace(",", " ")
    fonts = ["/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"]
    font = next((f for f in fonts if Path(f).exists()), None)
    vf = f"color=c=0x2b2d42:s={w}x{h}"
    draw = (f",drawtext=fontfile='{font}':text='{safe}':fontcolor=white:fontsize=40"
            f":x=(w-text_w)/2:y=(h-text_h)/2:box=1:boxcolor=black@0.4:boxborderw=20") if font else ""
    p = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                        "-i", f"{vf}{draw}", "-frames:v", "1", str(out)], capture_output=True, text=True)
    if p.returncode != 0:
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                        "-i", vf, "-frames:v", "1", str(out)], check=True)
    return out


def _download(url, name):
    out = OUT_DIR / name
    urllib.request.urlretrieve(url, out)
    return out


# ── 路由 ─────────────────────────────────────────────────────────
@app.route("/")
def index():
    return Response(PAGE_HTML, mimetype="text/html")


@app.route("/outputs/<path:fname>")
def outputs(fname):
    p = (OUT_DIR / fname).resolve()
    if not str(p).startswith(str(OUT_DIR.resolve())) or not p.exists():
        return "not found", 404
    return send_file(p)


@app.route("/api/meta")
def api_meta():
    return jsonify({"characters": list_characters(), "cameras": _camera_presets(),
                    "aspects": [{"value": k, "label": v["label"]} for k, v in ASPECTS.items()],
                    "vid_models": VID_MODELS, "resolutions": RESOLUTIONS, "durations": DURATIONS,
                    "res_default": RES_DEFAULT, "dur_default": DUR_DEFAULT, "topaz_per_s": TOPAZ_USD_PER_S,
                    "restyle_models": RESTYLE_MODELS, "reface_models": REFACE_MODELS,
                    "budget": ledger.budget(LEDGER_PROJECT),
                    "fal_ready": bool(os.environ.get("FAL_KEY") or os.environ.get("FAL_API_KEY"))})


_IMG_EXT = (".jpg", ".jpeg", ".png", ".webp", ".heic")


def _save_photo(f):
    ext = Path(f.filename).suffix.lower() or ".jpg"
    if ext not in _IMG_EXT:
        raise ValueError(f"不支持的格式 {ext}")
    token = hashlib.sha1((f.filename + str(time.time()) + os.urandom(4).hex()).encode()).hexdigest()[:12] + ext
    f.save(REF_DIR / token)
    return token


@app.route("/api/upload", methods=["POST"])
def api_upload():
    # 支持单张(photo)和多张(photos[]) —— 训练角色用多张
    multi = request.files.getlist("photos")
    if multi:
        try:
            refs = [_save_photo(f) for f in multi if f and f.filename]
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        if not refs:
            return jsonify({"error": "没有收到照片"}), 400
        return jsonify({"refs": refs})
    f = request.files.get("photo")
    if not f or not f.filename:
        return jsonify({"error": "没有收到照片"}), 400
    try:
        token = _save_photo(f)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ref": token})


@app.route("/api/train", methods=["POST"])
def api_train():
    """第1步：训练角色 —— 多张照片 → FLUX LoRA 身份锚（占位/真训）。"""
    from engine.character import CHARACTERS_DIR, _slug, train_character
    b = request.get_json(force=True)
    name = (b.get("name") or "").strip()
    refs = b.get("refs") or []
    mode = (b.get("mode") or "mock").strip()
    if not name:
        return jsonify({"error": "请给角色起个名字（如：爸爸）"}), 400
    paths = []
    for r in refs:
        p = (REF_DIR / r).resolve()
        if str(p).startswith(str(REF_DIR.resolve())) and p.exists():
            paths.append(p)
    try:
        if mode == "mock":
            slug = _slug(name)
            CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)
            prof = {"name": name, "slug": slug, "trigger_word": f"{slug}_person",
                    "lora_url": None, "mock": True, "n_photos": len(paths)}
            (CHARACTERS_DIR / f"{slug}.json").write_text(
                json.dumps(prof, ensure_ascii=False, indent=2), encoding="utf-8")
            cost = 0.0
        else:
            if len(paths) < 4:
                return jsonify({"error": f"真训练至少需要 4 张（建议 10–20 张多角度/表情），当前 {len(paths)} 张"}), 400
            prof = train_character(name, [str(p) for p in paths])
            cost = 2.0
    except Exception as e:
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 500
    ledger.log_gen(LEDGER_PROJECT, shot="train", status="kept", cost_usd=cost,
                   model="flux-lora-train" if mode != "mock" else "mock", ts=_now())
    return jsonify({"slug": prof["slug"], "name": prof["name"], "mock": (mode == "mock"),
                    "cost_usd": cost, "characters": list_characters(),
                    "budget": ledger.budget(LEDGER_PROJECT)})


@app.route("/api/upload_video", methods=["POST"])
def api_upload_video():
    f = request.files.get("video")
    if not f or not f.filename:
        return jsonify({"error": "没有收到视频"}), 400
    ext = Path(f.filename).suffix.lower() or ".mp4"
    if ext not in (".mp4", ".mov", ".webm", ".m4v"):
        return jsonify({"error": f"不支持的格式 {ext}"}), 400
    token = "vid_" + hashlib.sha1((f.filename + str(time.time())).encode()).hexdigest()[:12] + ext
    path = REF_DIR / token
    f.save(path)
    return jsonify({"ref": token, "duration_s": round(_vid_dur(path), 1)})


@app.route("/api/enhance", methods=["POST"])
def api_enhance():
    """DeepSeek 提示词扩写：大白话 → 详细生成指令。kind=scene/motion/restyle/reface。"""
    b = request.get_json(force=True)
    raw = (b.get("raw") or "").strip()
    kind = (b.get("kind") or "scene").strip()
    camera = (b.get("camera") or "").strip()
    cam = _camera_lookup(camera) if kind == "motion" else None
    # 运动镜头：允许只给运镜不打字（按运镜直接生成）
    if not raw and not (kind == "motion" and cam):
        return jsonify({"error": "先写一句你想要的内容（或先选一个运镜），我来扩写"}), 400
    user_msg = raw
    if cam:
        user_msg = (f"指定运镜：{cam['name']}（{cam.get('best_for','')}），"
                    f"英文运镜片段：{cam.get('prompt_fragment','')}。\n"
                    f"用户动作意图：{raw or '（未填，请根据该运镜补一个自然、克制的主体动作）'}")
    try:
        out = _deepseek(ENHANCE_SYSTEM.get(kind, ENHANCE_SYSTEM["scene"]), user_msg)
    except Exception as e:
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 500
    return jsonify({"prompt": out, "model": os.environ.get("DEEPSEEK_MODEL") or "deepseek-chat",
                    "camera": cam["name"] if cam else None})


@app.route("/api/keyframe", methods=["POST"])
def api_keyframe():
    b = request.get_json(force=True)
    source = (b.get("source") or "").strip()
    ref = (b.get("ref") or "").strip()
    scene = (b.get("scene") or "").strip()
    cam = (b.get("camera") or "").strip()
    aspect = (b.get("aspect") or "9:16").strip()
    mode = (b.get("mode") or "mock").strip()
    if not source:
        return jsonify({"error": "请先上传角色照片或选已训角色"}), 400
    if not scene:
        return jsonify({"error": "请填写场景描述"}), 400
    (kf_w, kf_h), _ = _dims(aspect)
    try:
        if mode == "mock":
            prompt = _kf_prompt(scene, cam, "the character, a person")
            local, cost, used = _mock_keyframe(prompt, source, kf_w, kf_h), 0.0, "mock"
        elif source == "upload":
            rp = (REF_DIR / ref).resolve()
            if not ref or not str(rp).startswith(str(REF_DIR.resolve())) or not rp.exists():
                return jsonify({"error": "上传照片不存在，请重新上传"}), 400
            prompt = _kf_prompt(scene, cam, "the person") + " " + realism_suffix()
            url = _nbp_keyframe(prompt, rp, aspect)
            local = _download(url, f"keyframe_{hashlib.sha1((prompt+ref).encode()).hexdigest()[:12]}.png")
            cost, used = 0.13, "nano-banana-pro"
        else:
            char = load_character(source)
            if not char.get("lora_url"):
                return jsonify({"error": "这是占位角色（未真训练）。请切到「真生成」前先真训练该角色，"
                                         "或改用「单张照片」入口。"}), 400
            from engine.providers.fal import FalProvider
            prov = FalProvider(); prov._require_key()
            prompt = _kf_prompt(scene, cam, f"{char['name']}, a person")
            url = prov._flux_lora_t2i(prompt, char["lora_url"], char["trigger_word"], kf_w, kf_h)
            local = _download(url, f"keyframe_{hashlib.sha1((prompt+source).encode()).hexdigest()[:12]}.png")
            cost, used = 0.01, "flux-lora"
    except Exception as e:
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 500
    ledger.log_gen(LEDGER_PROJECT, shot="keyframe", status="kept", cost_usd=cost, model=used, ts=_now())
    return jsonify({"keyframe": f"/outputs/{local.name}", "keyframe_file": local.name,
                    "model": used, "cost_usd": cost, "lint": seedance_lint.lint(prompt),
                    "budget": ledger.budget(LEDGER_PROJECT)})


@app.route("/api/animate", methods=["POST"])
def api_animate():
    b = request.get_json(force=True)
    kf_file = (b.get("keyframe_file") or "").strip()
    motion = (b.get("motion") or "").strip()
    aspect = (b.get("aspect") or "9:16").strip()
    vid_model = (b.get("vid_model") or "mock").strip()
    resolution = (b.get("resolution") or "720p").strip()
    duration = int(b.get("duration") or 5)
    if not kf_file:
        return jsonify({"error": "请先生成关键帧"}), 400
    if not motion:
        return jsonify({"error": "请填写运动描述"}), 400
    kf = (OUT_DIR / kf_file).resolve()
    if not str(kf).startswith(str(OUT_DIR.resolve())) or not kf.exists():
        return jsonify({"error": "关键帧文件不存在"}), 400
    _, (vw, vh) = _dims(aspect)
    want_4k = resolution.lower() in ("4k", "2160p")
    base_res = "1080p" if want_4k else resolution   # 4K：先出 1080p 再 Topaz 升采样
    os.environ["FAL_RESOLUTION"] = base_res          # FalProvider 初始化时读这个
    if vid_model == "mock":
        prov, model = get_provider("mock"), "seedance-2.0-i2v"
    else:
        prov, model = get_provider("fal"), vid_model
    try:
        res = prov.submit(GenSpec(kind="i2v", model=model, image_path=str(kf),
                                  prompt=motion, duration_s=duration, width=vw, height=vh))
        cost = res.cost_usd
        out_path, used = res.local_path, res.model
        if want_4k and vid_model != "mock":         # 4K 第二步：Topaz 升采样
            from engine.providers.fal import FalProvider
            up = FalProvider(); up._require_key()
            up_url = up.topaz_upscale_video(res.local_path)
            if not up_url:
                raise RuntimeError("Topaz 升采样未返回视频")
            out_path = _download(up_url, f"up4k_{hashlib.sha1((kf_file+motion).encode()).hexdigest()[:12]}.mp4")
            cost = round(cost + res.duration_s * TOPAZ_USD_PER_S, 4)
            used = f"{res.model}+topaz4k"
    except Exception as e:
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 500
    final = OUT_DIR / f"film_{hashlib.sha1((motion+kf_file+resolution).encode()).hexdigest()[:12]}.mp4"
    shutil.copy(out_path, final)
    ledger.log_gen(LEDGER_PROJECT, shot="i2v", status="kept", cost_usd=cost, model=used, ts=_now())
    return jsonify({"video": f"/outputs/{final.name}", "cost_usd": cost, "duration_s": res.duration_s,
                    "model": used, "lint": seedance_lint.lint(motion), "budget": ledger.budget(LEDGER_PROJECT)})


@app.route("/api/restyle", methods=["POST"])
def api_restyle():
    """换场景 2A：上传视频 + 一句话 → v2v 编辑（可选模型，Kling O1 保原音）。"""
    b = request.get_json(force=True)
    ref = (b.get("ref") or "").strip()
    prompt = (b.get("prompt") or "").strip()
    keep_audio = bool(b.get("keep_audio", True))
    model = (b.get("model") or "mock").strip()
    m = RESTYLE_MAP.get(model)
    if not m:
        return jsonify({"error": f"未知模型 {model}"}), 400
    if not ref:
        return jsonify({"error": "请先上传一段视频"}), 400
    if not prompt:
        return jsonify({"error": "请描述要把场景/背景换成什么"}), 400
    vp = (REF_DIR / ref).resolve()
    if not str(vp).startswith(str(REF_DIR.resolve())) or not vp.exists():
        return jsonify({"error": "视频不存在，请重新上传"}), 400
    trim = bool(b.get("trim"))
    key = hashlib.sha1((ref + prompt + model + str(trim)).encode()).hexdigest()[:12]
    try:
        if model == "mock":
            out = OUT_DIR / f"restyle_{key}.mp4"
            shutil.copy(vp, out)  # 占位：原样返回，零成本跑通流程
            cost = 0.0
        else:
            use_vp, bill_s, err = _enforce_dur(vp, m, trim)
            if err:
                return jsonify({"error": err, "need_trim": True}), 400
            url = _v2v_edit(m["endpoint"], use_vp, prompt, keep_audio, m["keep_audio"])
            if not url:
                raise RuntimeError("模型未返回视频 URL")
            out = _download(url, f"restyle_{key}.mp4")
            cost = round(bill_s * m["per_s"], 2)
    except Exception as e:
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 500
    ledger.log_gen(LEDGER_PROJECT, shot="restyle", status="kept", cost_usd=cost, model=model, ts=_now())
    return jsonify({"video": f"/outputs/{out.name}", "cost_usd": cost,
                    "budget": ledger.budget(LEDGER_PROJECT)})


@app.route("/api/reface", methods=["POST"])
def api_reface():
    """换脸 2B：口播视频 + 目标人脸 → 首帧改脸 → Kling Motion Control。
    real 为实验：先抽首帧用 NBP 把脸改成目标（已验证），再走 motion-control（端点待核对）。"""
    b = request.get_json(force=True)
    ref = (b.get("ref") or "").strip()        # 口播视频 token
    face_ref = (b.get("face_ref") or "").strip()  # 目标人脸照片 token（可选）
    face_slug = (b.get("face_slug") or "").strip()  # 已训角色（可选）
    prompt = (b.get("prompt") or "").strip()  # 目标人/场景描述
    model = (b.get("model") or "mock").strip()
    m = REFACE_MAP.get(model)
    if not m:
        return jsonify({"error": f"未知模型 {model}"}), 400
    if not ref:
        return jsonify({"error": "请先上传口播视频"}), 400
    vp = (REF_DIR / ref).resolve()
    if not str(vp).startswith(str(REF_DIR.resolve())) or not vp.exists():
        return jsonify({"error": "视频不存在，请重新上传"}), 400
    if model != "mock" and not face_ref and not face_slug and not prompt:
        return jsonify({"error": "真换脸需要上传目标人脸照片、选已训角色，或用文字描述目标人"}), 400
    trim = bool(b.get("trim"))
    key = hashlib.sha1((ref + face_ref + face_slug + prompt + model + str(trim)).encode()).hexdigest()[:12]
    try:
        if model == "mock":
            out = OUT_DIR / f"reface_{key}.mp4"
            shutil.copy(vp, out)
            cost = 0.0
        else:
            use_vp, bill_s, derr = _enforce_dur(vp, m, trim)
            if derr:
                return jsonify({"error": derr, "need_trim": True}), 400
            ff = _first_frame(use_vp)          # 1) 抽首帧
            edit_prompt = (prompt or "this exact person") + " " + realism_suffix()
            face_uris = [_data_uri(ff)]
            extra_cost = 0.13
            if face_ref:                       # 2a) 目标脸来自上传照片
                fp = (REF_DIR / face_ref).resolve()
                if not str(fp).startswith(str(REF_DIR.resolve())) or not fp.exists():
                    return jsonify({"error": "目标人脸照片不存在"}), 400
                face_uris.append(_data_uri(fp))
            elif face_slug:                    # 2b) 目标脸来自已训角色 → FLUX-LoRA 出正脸
                char = load_character(face_slug)
                if not char.get("lora_url"):
                    return jsonify({"error": "该角色是占位（未真训练），无法用于换脸"}), 400
                from engine.providers.fal import FalProvider
                prov = FalProvider(); prov._require_key()
                portrait = prov._flux_lora_t2i(f"{char['name']}, frontal face portrait, neutral expression",
                                               char["lora_url"], char["trigger_word"], 768, 768)
                face_uris.append(portrait)
                extra_cost += 0.01
            full = (("Replace the person's face and hair with THIS person (keep identity identical "
                     "to the reference). " if len(face_uris) > 1 else "") + edit_prompt)
            ff_url = _poll(_post("https://queue.fal.run/fal-ai/nano-banana-pro/edit",
                          {"prompt": full, "image_urls": face_uris,
                           "num_images": 1, "output_format": "jpeg"}))["images"][0]["url"]
            url = _motion_control(m["endpoint"], use_vp, ff_url, m["mode_param"])  # 3) motion control
            if not url:
                raise RuntimeError("模型未返回视频 URL")
            out = _download(url, f"reface_{key}.mp4")
            cost = round(bill_s * m["per_s"] + extra_cost, 2)
    except Exception as e:
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 500
    ledger.log_gen(LEDGER_PROJECT, shot="reface", status="kept", cost_usd=cost, model=model, ts=_now())
    return jsonify({"video": f"/outputs/{out.name}", "cost_usd": cost,
                    "budget": ledger.budget(LEDGER_PROJECT)})


PAGE_HTML = r"""<!DOCTYPE html>
<html lang="zh"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Open Edit · 出片</title>
<style>
  :root{--bg:#0f1117;--card:#1a1d29;--line:#2a2e3d;--ink:#e8eaf0;--sub:#9aa0b4;
        --accent:#6c8cff;--warn:#ffb454;--danger:#ff6b6b;--ok:#7ed98a;}
  *{box-sizing:border-box;} body{margin:0;background:var(--bg);color:var(--ink);
    font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.5;}
  .wrap{max-width:720px;margin:0 auto;padding:16px 16px 60px;}
  h1{font-size:19px;margin:4px 0 12px;}
  .tabs{display:flex;gap:8px;margin-bottom:14px;}
  .tabs button{flex:1;padding:11px 0;font-size:15px;font-weight:600;border-radius:10px;
    background:var(--card);border:1px solid var(--line);color:var(--sub);cursor:pointer;}
  .tabs button.on{background:var(--accent);border-color:var(--accent);color:#fff;}
  .card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin-bottom:14px;}
  .lbl{font-size:13px;color:var(--sub);margin:10px 0 6px;} .lbl:first-child{margin-top:0;}
  select,textarea{width:100%;background:#0f1117;color:var(--ink);border:1px solid var(--line);
    border-radius:10px;padding:11px;font-size:15px;font-family:inherit;} textarea{resize:vertical;min-height:60px;}
  .row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;} .row>*{flex:1;min-width:0;}
  button{background:var(--accent);color:#fff;border:0;border-radius:10px;padding:12px 16px;
    font-size:15px;font-weight:600;cursor:pointer;} button:disabled{opacity:.5;cursor:not-allowed;}
  button.sec{background:#2a2e3d;} button.ghost{background:transparent;border:1px solid var(--line);color:var(--sub);font-weight:500;}
  .seg{display:flex;gap:8px;} .seg button{flex:1;padding:9px 0;font-size:14px;font-weight:500;
    background:#0f1117;border:1px solid var(--line);color:var(--sub);}
  .seg button.on{background:var(--accent);color:#fff;border-color:var(--accent);}
  .uprow{display:flex;gap:12px;align-items:center;}
  .drop{flex:1;border:1px dashed var(--line);border-radius:12px;padding:16px;text-align:center;
    color:var(--sub);font-size:13px;cursor:pointer;background:#0f1117;} .drop.on{border-color:var(--accent);color:var(--ink);}
  .upthumb{width:60px;height:60px;border-radius:10px;object-fit:cover;display:none;border:1px solid var(--line);}
  .chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;}
  .chip{padding:6px 12px;border-radius:20px;border:1px solid var(--line);background:#0f1117;color:var(--sub);font-size:13px;cursor:pointer;}
  .chip.on{border-color:var(--accent);color:#fff;background:var(--accent);}
  .canvas{background:#0b0d13;border:1px solid var(--line);border-radius:14px;width:100%;aspect-ratio:9/16;
    max-height:60vh;display:flex;align-items:center;justify-content:center;overflow:hidden;margin:4px auto 10px;}
  .canvas .ph{color:var(--sub);font-size:13px;text-align:center;padding:24px;}
  .canvas img,.canvas video{max-width:100%;max-height:100%;object-fit:contain;}
  .hint{font-size:12px;color:var(--sub);margin-top:6px;} .prov-fal{color:var(--danger);}
  .cost{font-size:13px;color:var(--warn);margin-top:8px;}
  .lint{font-size:12px;color:var(--warn);margin-top:8px;background:#2a230f;border-radius:8px;padding:8px 10px;}
  .lint.ok{color:var(--ok);background:#13251a;} .err{color:var(--danger);font-size:13px;margin-top:8px;}
  .budget{font-size:13px;color:var(--sub);text-align:center;padding:12px;border:1px solid var(--line);border-radius:12px;}
  .budget b{color:var(--ink);} .center{text-align:center;}
  .spin{display:inline-block;width:14px;height:14px;border:2px solid #fff;border-top-color:transparent;
    border-radius:50%;animation:s .7s linear infinite;vertical-align:-2px;margin-right:6px;} @keyframes s{to{transform:rotate(360deg);}}
  .soon{text-align:center;color:var(--sub);padding:40px 20px;font-size:14px;}
  .enh{background:#23304d;color:#bcd0ff;border:1px solid #34487a;font-size:13px;font-weight:500;
    padding:7px 12px;margin-top:8px;}
</style></head>
<body><div class="wrap">
  <h1>Open Edit · 出片</h1>
  <div class="tabs">
    <button data-t="create" class="on">出片</button>
    <button data-t="restyle">换场景</button>
    <button data-t="reface">换脸</button>
  </div>

  <!-- ============ TAB: 出片 ============ -->
  <div id="tab-create">
    <!-- 第 1 步：训练 / 选角色 -->
    <div class="card">
      <div class="lbl">第 1 步 · 角色（先训练锁住同一张脸，或选已训角色）</div>
      <div class="chips" id="chips"></div>
      <div class="chips" style="margin-top:10px">
        <div class="chip" id="actTrain" style="border-style:dashed">＋ 训练新角色</div>
        <div class="chip" id="actUpload" style="border-style:dashed">📷 用单张照片（不训练）</div>
      </div>

      <!-- 训练新角色 -->
      <div id="trainBox" style="display:none;margin-top:12px">
        <div class="drop" id="tdrop">点此上传 / 拖入多张照片<br>
          <span style="font-size:11px">建议 10–20 张：正脸 / 侧脸 / 不同表情，越多越像</span></div>
        <input type="file" id="tfiles" accept="image/*" multiple style="display:none">
        <div class="chips" id="tthumbs" style="margin-top:8px"></div>
        <div class="lbl">角色名</div>
        <input id="tname" placeholder="例：爸爸" style="width:100%;background:#0f1117;color:var(--ink);
          border:1px solid var(--line);border-radius:10px;padding:11px;font-size:15px;">
        <div class="row" style="margin-top:12px">
          <div class="seg" id="tmodeSeg" style="flex:1.4"></div>
          <button id="btnTrain" style="flex:1">⚙ 训练角色</button>
        </div>
        <div class="hint" id="tmodeHint"></div><div class="err" id="tErr"></div>
      </div>

      <!-- 单张照片（不训练，NBP 改图锁脸） -->
      <div id="uploadBox" style="display:none;margin-top:12px">
        <div class="uprow">
          <div class="drop" id="drop">点此上传 / 拖入正脸照片<br><span style="font-size:11px">jpg / png / heic</span></div>
          <img id="upthumb" class="upthumb"><input type="file" id="file" accept="image/*" style="display:none">
        </div>
      </div>

      <div class="lbl">画面比例</div><div class="seg" id="aspectSeg"></div>
    </div>
    <div class="card">
      <div class="lbl">第 2 步 · 场景描述（关键帧画面长什么样，一句话）</div>
      <textarea id="scene" placeholder="例：暖烛光牛排馆，他坐在木桌前，浅景深"></textarea>
      <button class="enh" data-k="scene" data-t="scene">✨ 生成提示词</button>
      <div class="row" style="margin-top:12px">
        <div class="seg" id="modeSeg" style="flex:1.4"></div>
        <button id="btnKeyframe" style="flex:1">✦ 生成关键帧</button>
      </div>
      <div class="hint" id="modeHint"></div><div class="err" id="kfErr"></div>
    </div>
    <div class="canvas" id="canvas"><div class="ph" id="canvasPh">关键帧 / 成片预览出现在这里</div>
      <img id="canvasImg" style="display:none"><video id="canvasVideo" style="display:none" controls playsinline></video></div>
    <div class="center" id="kfActions" style="display:none;margin-bottom:14px">
      <button class="ghost" id="btnRegen">↻ 不满意，重新生成关键帧</button>
      <div class="cost" id="kfCost"></div><div id="kfLint"></div></div>
    <div class="card" id="animCard" style="opacity:.5;pointer-events:none">
      <div class="lbl">第 3 步 · 相机运镜预设（先选运镜，提示词按它生成）</div><select id="camera"></select>
      <div class="lbl">运动描述（可只写动作意图，运镜交给上面预设）</div>
      <textarea id="motion" placeholder="例：他缓缓抬眼看向镜头（运镜从上面选 Dolly In）"></textarea>
      <button class="enh" data-k="motion" data-t="motion">✨ 按运镜生成提示词</button>
      <div class="row" style="margin-top:10px">
        <div><div class="lbl" style="margin-top:0">分辨率</div><div class="seg" id="resSeg"></div></div>
        <div><div class="lbl" style="margin-top:0">时长</div><div class="seg" id="durSeg"></div></div>
      </div>
      <div class="row" style="margin-top:12px">
        <select id="vidModel" style="flex:1.4"></select>
        <button id="btnAnimate" class="sec" style="flex:1">▶ 出片</button>
      </div>
      <div class="hint prov-fal" id="vidHint"></div><div class="err" id="anErr"></div>
      <div class="cost" id="anCost"></div><div id="anLint"></div>
    </div>
  </div>

  <!-- ============ TAB: 换场景 (2A) ============ -->
  <div id="tab-restyle" style="display:none">
    <div class="card">
      <div class="lbl">上传一段视频（要被换场景/背景的）</div>
      <div class="uprow">
        <div class="drop" id="vdrop">点此上传 / 拖入视频<br><span style="font-size:11px">mp4 / mov，建议 3–10 秒</span></div>
        <input type="file" id="vfile" accept="video/*" style="display:none">
      </div>
      <div class="hint" id="vinfo"></div>
      <label id="rTrimWrap" style="display:none;align-items:center;gap:6px;color:var(--warn);font-size:13px;margin-top:6px">
        <input type="checkbox" id="rTrim" checked style="width:auto"> 超长自动截取前 <span id="rTrimMax">10</span> 秒</label>
      <div class="lbl">换成什么（一句话）</div>
      <textarea id="rprompt" placeholder="例：把背景换成温暖高级的牛排馆，木饰砖墙暖灯，保持人物动作和镜头不变"></textarea>
      <button class="enh" data-k="restyle" data-t="rprompt">✨ 生成提示词</button>
      <div class="lbl">模型</div><select id="rModel"></select>
      <div class="row" style="margin-top:10px;align-items:center">
        <label style="flex:none;display:flex;align-items:center;gap:6px;color:var(--sub);font-size:13px">
          <input type="checkbox" id="keepAudio" checked style="width:auto"> 保留原声/口播</label>
        <button id="btnRestyle" style="flex:1">▶ 换场景</button>
      </div>
      <div class="hint" id="rmodeHint"></div><div class="err" id="rErr"></div>
    </div>
    <div class="canvas" id="rcanvas" style="aspect-ratio:9/16"><div class="ph" id="rph">上传后这里预览原视频，换完播放结果</div>
      <video id="rvideo" style="display:none" controls playsinline></video></div>
    <div class="center"><div class="cost" id="rCost"></div></div>
  </div>

  <!-- ============ TAB: 换脸 (2B) ============ -->
  <div id="tab-reface" style="display:none">
    <div class="card">
      <div class="lbl">上传口播视频（要被换脸的人物视频）</div>
      <div class="uprow">
        <div class="drop" id="fvdrop">点此上传 / 拖入视频<br><span style="font-size:11px">mp4 / mov，单人、上半身清晰，≤30 秒</span></div>
        <input type="file" id="fvfile" accept="video/*" style="display:none">
      </div>
      <div class="hint" id="fvinfo"></div>
      <label id="fTrimWrap" style="display:none;align-items:center;gap:6px;color:var(--warn);font-size:13px;margin-top:6px">
        <input type="checkbox" id="fTrim" checked style="width:auto"> 超长自动截取前 <span id="fTrimMax">10</span> 秒</label>
      <div class="lbl">目标人脸（上传你的正脸照片，或选已训角色，可选）</div>
      <div class="uprow">
        <div class="drop" id="fdrop">点此上传目标人脸<br><span style="font-size:11px">jpg / png / heic</span></div>
        <img id="fthumb" class="upthumb"><input type="file" id="ffile" accept="image/*" style="display:none">
      </div>
      <div class="chips" id="fchips" style="margin-top:8px"></div>
      <div class="lbl">目标描述（可选：换成谁 / 换什么场景）</div>
      <textarea id="fprompt" placeholder="例：换成一位中年亚洲男性厨师，戴黑围裙，暖光牛排馆背景"></textarea>
      <button class="enh" data-k="reface" data-t="fprompt">✨ 生成提示词</button>
      <div class="lbl">模型</div><select id="fModel"></select>
      <button id="btnReface" style="width:100%;margin-top:12px">▶ 换脸</button>
      <div class="hint" id="fmodeHint"></div><div class="err" id="fErr"></div>
    </div>
    <div class="canvas" id="fcanvas" style="aspect-ratio:9/16"><div class="ph" id="fph">上传后预览原视频，换完播放结果</div>
      <video id="fvideo" style="display:none" controls playsinline></video></div>
    <div class="center"><div class="cost" id="fCost"></div></div>
  </div>

  <div class="budget" id="budget"></div>
</div>
<script>
const $=id=>document.getElementById(id);
let meta=null,lastKeyframeFile=null,aspect="9:16",mode="mock",source="",refToken="",
    vidModels=[],resolution="720p",duration=5,vidToken="",topazPerS=0.08,
    tmode="mock",trainRefs=[],
    restyleModels=[],refaceModels=[],fvidToken="",fFaceToken="",fFaceSlug="",
    rVidDur=0,fVidDur=0;
const AR={"9:16":"9/16","16:9":"16/9","1:1":"1/1"};

function lintHtml(l){if(!l)return"";const m=[].concat(l.errors||[],l.warnings||[]);
  return(l.ok&&!m.length)?'<div class="lint ok">✓ prompt 预检通过（'+l.score+'分）</div>'
    :'<div class="lint">prompt 预检（'+l.score+'分）：<br>· '+m.join('<br>· ')+'</div>';}
function renderBudget(b){$("budget").innerHTML='累计生成 <b>'+b.generations+'</b> · 保留 <b>'+b.kept+
  '</b> · 花费 <b>$'+b.spent_usd+'</b> · keeper <b>'+(b.overall_keep_rate*100).toFixed(0)+'%</b>';}

// tabs
[...document.querySelectorAll(".tabs button")].forEach(b=>b.addEventListener("click",()=>{
  [...document.querySelectorAll(".tabs button")].forEach(x=>x.classList.toggle("on",x===b));
  ["create","restyle","reface"].forEach(t=>$("tab-"+t).style.display=(t===b.dataset.t)?"block":"none");}));

function setAspect(a){aspect=a;$("canvas").style.aspectRatio=AR[a];
  [...$("aspectSeg").children].forEach(b=>b.classList.toggle("on",b.dataset.v===a));}
function kfCost(){return mode==="mock"?0:(source==="upload"?0.13:0.01);}
function setMode(m){mode=m;[...$("modeSeg").children].forEach(b=>b.classList.toggle("on",b.dataset.v===m));
  $("modeHint").innerHTML=m==="mock"?"占位：零成本":(source==="upload"
    ?'<span class="prov-fal">💸 上传脸用 Nano Banana Pro，约 $0.13/张</span>'
    :'<span class="prov-fal">💸 已训角色用 FLUX+LoRA 锁脸，约 $0.01/张</span>');
  $("btnKeyframe").textContent="✦ 生成关键帧"+(kfCost()?" (~$"+kfCost()+")":"");}
function renderChips(chars){
  $("chips").innerHTML=chars.map(c=>'<div class="chip" data-s="'+c.slug+'">'+
    (c.trained?'✓ ':'○ ')+c.name+(c.trained?'':'（占位）')+'</div>').join("")
    || '<span style="color:var(--sub);font-size:13px">还没有角色，点下面「训练新角色」开始</span>';
  [...$("chips").children].forEach(c=>{if(!c.dataset.s)return;
    c.addEventListener("click",()=>{$("upthumb").style.display="none";refToken="";
      $("trainBox").style.display="none";$("uploadBox").style.display="none";pickSource(c.dataset.s,false);});});}
function pickSource(s,up){source=s;
  [...$("chips").children].forEach(c=>c.dataset.s&&c.classList.toggle("on",!up&&c.dataset.s===s));
  $("drop")&&$("drop").classList.toggle("on",up);setMode(mode);}
function is4k(){return resolution.toLowerCase()==="4k";}
function curVid(){return vidModels.find(x=>x.value===$("vidModel").value)||{};}
function vidCostEst(){const m=curVid();if(!m.value||m.value==="mock")return 0;
  let c=m.per_s!=null?m.per_s*duration:m.flat5*Math.ceil(duration/5);
  if(is4k())c+=topazPerS*duration;  // 4K：+Topaz 升采样
  return +c.toFixed(2);}
// Kling 不吃分辨率参数（由关键帧/比例决定）→ 灰掉 480/720/1080，只留 4K(升采样)
function updateResForModel(){const m=curVid(),native=m.res_native!==false;
  [...$("resSeg").children].forEach(b=>{const is4=b.dataset.v.toLowerCase()==="4k";
    const off=!native&&!is4;b.disabled=off;b.style.opacity=off?".35":"";});
  if(!native&&!is4k()){const f=[...$("resSeg").children].find(b=>b.dataset.v.toLowerCase()==="4k");
    /* 不强切，只提示；保留用户选择 */}}
function refreshAnimBtn(){updateResForModel();
  const c=vidCostEst();$("btnAnimate").textContent="▶ 出片"+(c?" (~$"+c+")":"");
  const m=curVid();
  $("vidHint").innerHTML=(m.value&&m.value!=="mock")
    ?('💸 真生成，需几分钟'
      +(m.res_native===false?'；Kling 分辨率由关键帧决定，480/720/1080 仅 Seedance 生效':'')
      +(is4k()?'；4K=先出'+(m.res_native===false?'原生':'1080p')+'帧再 Topaz 升采样（+$'+topazPerS+'/秒）':'')):'';}

async function loadMeta(){
  meta=await(await fetch("/api/meta")).json();
  renderChips(meta.characters);
  $("camera").innerHTML='<option value="">（不指定运镜）</option>'+meta.cameras.map(c=>'<option value="'+c.name+'">'+c.name+' — '+c.best_for+'</option>').join("");
  $("aspectSeg").innerHTML=meta.aspects.map(a=>'<button data-v="'+a.value+'">'+a.label+'</button>').join("");
  [...$("aspectSeg").children].forEach(b=>b.addEventListener("click",()=>setAspect(b.dataset.v)));
  $("modeSeg").innerHTML='<button data-v="mock">占位·免费</button><button data-v="real">真生成</button>';
  [...$("modeSeg").children].forEach(b=>b.addEventListener("click",()=>setMode(b.dataset.v)));
  topazPerS=meta.topaz_per_s||0.08;
  $("resSeg").innerHTML=meta.resolutions.map(r=>'<button data-v="'+r+'">'+r+'</button>').join("");
  [...$("resSeg").children].forEach(b=>b.addEventListener("click",()=>{if(b.disabled)return;resolution=b.dataset.v;
    [...$("resSeg").children].forEach(x=>x.classList.toggle("on",x===b));refreshAnimBtn();}));
  $("durSeg").innerHTML=meta.durations.map(d=>'<button data-v="'+d+'">'+d+'秒</button>').join("");
  [...$("durSeg").children].forEach(b=>b.addEventListener("click",()=>{duration=+b.dataset.v;
    [...$("durSeg").children].forEach(x=>x.classList.toggle("on",x===b));refreshAnimBtn();}));
  resolution=meta.res_default||"720p";duration=meta.dur_default||5;
  vidModels=meta.vid_models;
  $("vidModel").innerHTML=vidModels.map(m=>'<option value="'+m.value+'">'+m.label+'</option>').join("");
  $("vidModel").addEventListener("change",refreshAnimBtn);
  // 换场景 / 换脸 模型下拉
  restyleModels=meta.restyle_models;refaceModels=meta.reface_models;
  $("rModel").innerHTML=restyleModels.map(m=>'<option value="'+m.value+'">'+m.label+'</option>').join("");
  $("rModel").addEventListener("change",setRestyleHint);
  $("fModel").innerHTML=refaceModels.map(m=>'<option value="'+m.value+'">'+m.label+'</option>').join("");
  $("fModel").addEventListener("change",setRefaceHint);
  $("fchips").innerHTML=meta.characters.filter(c=>c.trained).map(c=>'<div class="chip" data-s="'+c.slug+'">✓ '+c.name+'</div>').join("");
  [...$("fchips").children].forEach(c=>c.addEventListener("click",()=>{
    fFaceSlug=(fFaceSlug===c.dataset.s)?"":c.dataset.s;fFaceToken="";
    $("fthumb").style.display="none";$("fdrop").classList.remove("on");
    [...$("fchips").children].forEach(x=>x.classList.toggle("on",x.dataset.s===fFaceSlug&&fFaceSlug));}));
  $("tmodeSeg").innerHTML='<button data-v="mock">占位·免费</button><button data-v="real">真训(~$2)</button>';
  [...$("tmodeSeg").children].forEach(b=>b.addEventListener("click",()=>setTmode(b.dataset.v)));
  setTmode("mock");
  setAspect("9:16");setMode("mock");
  const rb=[...$("resSeg").children].find(b=>b.dataset.v===resolution)||$("resSeg").children[0];rb.classList.add("on");
  const db=[...$("durSeg").children].find(b=>+b.dataset.v===duration)||$("durSeg").children[0];db.classList.add("on");
  refreshAnimBtn();setRestyleHint();setRefaceHint();renderBudget(meta.budget);
}
function setRestyleHint(){const m=restyleModels.find(x=>x.value===$("rModel").value)||{};
  $("keepAudio").disabled=!m.keep_audio;$("keepAudio").parentElement.style.opacity=m.keep_audio?"1":".4";
  $("btnRestyle").textContent="▶ 换场景"+(m.per_s?" (~$"+m.per_s+"/秒)":"");
  $("rmodeHint").innerHTML=m.value==="mock"?"占位：原样返回，零成本":
    (m.validated?'<span class="prov-fal">💸 真生成，约 $'+m.per_s+'/秒（按视频时长）</span>':
     '<span class="warn" style="color:var(--warn)">⚠ 实验模型：端点未在本项目实测，可能需核对；'+(m.keep_audio?'':'不保原音；')+'约 $'+m.per_s+'/秒</span>');
  refreshRestyle(m);}
function refreshRestyle(m){m=m||restyleModels.find(x=>x.value===$("rModel").value)||{};
  const over=m.max_s&&rVidDur>m.max_s+0.2;
  $("rTrimWrap").style.display=over?"flex":"none";if(m.max_s)$("rTrimMax").textContent=m.max_s;
  if(rVidDur){const bill=m.max_s?Math.min(rVidDur,m.max_s):rVidDur;
    $("vinfo").innerHTML="时长 "+rVidDur+" 秒"+(m.per_s?" · 预估 $"+(bill*m.per_s).toFixed(2):"")+
      (over?'　<span style="color:var(--warn)">⚠ 超 '+m.max_s+'秒上限，将自动截取前 '+m.max_s+'秒</span>':
       (m.max_s?'　<span style="color:var(--sub)">（'+(m.min_s||0)+'–'+m.max_s+'秒）</span>':''));}}
function setRefaceHint(){const m=refaceModels.find(x=>x.value===$("fModel").value)||{};
  $("btnReface").textContent="▶ 换脸"+(m.per_s?" (~$"+m.per_s+"/秒+改脸)":"");
  $("fmodeHint").innerHTML=m.value==="mock"?"占位：原样返回，零成本（先跑通流程）":
    '<span class="warn" style="color:var(--warn)">⚠ 实验：先抽首帧用 Nano Banana Pro 改脸（已验证），再走 Kling Motion Control（端点待核对，可能失败）。约 $'+m.per_s+'/秒</span>';
  refreshReface(m);}
function refreshReface(m){m=m||refaceModels.find(x=>x.value===$("fModel").value)||{};
  const over=m.max_s&&fVidDur>m.max_s+0.2;
  $("fTrimWrap").style.display=over?"flex":"none";if(m.max_s)$("fTrimMax").textContent=m.max_s;
  if(fVidDur)$("fvinfo").innerHTML="时长 "+fVidDur+" 秒"+
    (over?'　<span style="color:var(--warn)">⚠ 超 '+m.max_s+'秒上限，将自动截取前 '+m.max_s+'秒</span>':
     (m.max_s?'　<span style="color:var(--sub)">（'+(m.min_s||0)+'–'+m.max_s+'秒）</span>':''));}

// 第1步：训练 / 单张 切换
$("actTrain").addEventListener("click",()=>{const open=$("trainBox").style.display==="none";
  $("trainBox").style.display=open?"block":"none";$("uploadBox").style.display="none";
  $("actTrain").classList.toggle("on",open);$("actUpload").classList.remove("on");});
$("actUpload").addEventListener("click",()=>{const open=$("uploadBox").style.display==="none";
  $("uploadBox").style.display=open?"block":"none";$("trainBox").style.display="none";
  $("actUpload").classList.toggle("on",open);$("actTrain").classList.remove("on");});

function setTmode(m){tmode=m;[...$("tmodeSeg").children].forEach(b=>b.classList.toggle("on",b.dataset.v===m));
  $("tmodeHint").innerHTML=m==="mock"?"占位：只登记角色名，跑通流程（占位档出片要配占位关键帧）":
    '<span class="prov-fal">💸 真训练 FLUX LoRA，约 $2、5–10 分钟，得到可复用的锁脸锚</span>';
  $("btnTrain").textContent="⚙ 训练角色"+(m==="mock"?"":" (~$2)");}

// 训练：多张照片上传
$("tdrop").addEventListener("click",()=>$("tfiles").click());
$("tfiles").addEventListener("change",async e=>{const fs=[...e.target.files];if(!fs.length)return;
  const fd=new FormData();fs.forEach(f=>fd.append("photos",f));$("tdrop").textContent="上传中…";
  try{const r=await fetch("/api/upload",{method:"POST",body:fd});const d=await r.json();if(!r.ok)throw new Error(d.error);
    trainRefs=trainRefs.concat(d.refs);
    $("tthumbs").innerHTML+=fs.map(f=>'<img class="upthumb" style="display:inline-block;width:48px;height:48px" src="'+URL.createObjectURL(f)+'">').join("");
    $("tdrop").innerHTML="✓ 已选 "+trainRefs.length+" 张，点可继续添加<br><span style='font-size:11px'>越多越像</span>";
  }catch(err){$("tdrop").textContent="上传失败："+err.message;}});

$("btnTrain").addEventListener("click",async()=>{const btn=$("btnTrain");$("tErr").textContent="";
  if(!$("tname").value.trim()){$("tErr").textContent="请给角色起个名字";return;}
  if(tmode==="real"&&trainRefs.length<4){$("tErr").textContent="真训练至少 4 张（建议 10–20 张）";return;}
  btn.disabled=true;btn.innerHTML='<span class="spin"></span>'+(tmode==="mock"?"登记中…":"训练中…（约 5–10 分钟，勿关页面）");
  try{const r=await fetch("/api/train",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({name:$("tname").value,refs:trainRefs,mode:tmode})});
    const d=await r.json();if(!r.ok)throw new Error(d.error||"训练失败");
    renderChips(d.characters);$("trainBox").style.display="none";$("actTrain").classList.remove("on");
    trainRefs=[];$("tthumbs").innerHTML="";$("tname").value="";
    $("tdrop").innerHTML="点此上传 / 拖入多张照片<br><span style='font-size:11px'>建议 10–20 张</span>";
    pickSource(d.slug,false);renderBudget(d.budget);
  }catch(e){$("tErr").textContent=e.message;}finally{btn.disabled=false;setTmode(tmode);}});

// 单张照片上传（不训练）
$("drop").addEventListener("click",()=>$("file").click());
$("file").addEventListener("change",async e=>{const f=e.target.files[0];if(!f)return;
  const fd=new FormData();fd.append("photo",f);$("drop").textContent="上传中…";
  try{const r=await fetch("/api/upload",{method:"POST",body:fd});const d=await r.json();if(!r.ok)throw new Error(d.error);
    refToken=d.ref;pickSource("upload",true);$("upthumb").src=URL.createObjectURL(f);$("upthumb").style.display="block";
    $("drop").innerHTML="✓ 已上传，点可换<br><span style='font-size:11px'>用这张脸</span>";
  }catch(err){$("drop").textContent="上传失败："+err.message;}});

async function genKeyframe(){const btn=$("btnKeyframe");$("kfErr").textContent="";
  if(!source){$("kfErr").textContent="请先上传照片或选已训角色";return;}
  if(!$("scene").value.trim()){$("kfErr").textContent="请填写场景描述";return;}
  [btn,$("btnRegen")].forEach(b=>b.disabled=true);btn.innerHTML='<span class="spin"></span>生成中…';
  try{const r=await fetch("/api/keyframe",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({source,ref:refToken,scene:$("scene").value,camera:"",aspect,mode})});
    const d=await r.json();if(!r.ok)throw new Error(d.error||"生成失败");
    lastKeyframeFile=d.keyframe_file;const s=d.keyframe+"?t="+Date.now();
    $("canvasImg").src=s;$("canvasImg").style.display="block";$("canvasVideo").style.display="none";$("canvasPh").style.display="none";
    $("kfActions").style.display="block";$("kfCost").textContent="关键帧成本：$"+d.cost_usd+"（"+d.model+"）";$("kfLint").innerHTML=lintHtml(d.lint);
    $("animCard").style.opacity="1";$("animCard").style.pointerEvents="auto";renderBudget(d.budget);
  }catch(e){$("kfErr").textContent=e.message;}
  finally{[btn,$("btnRegen")].forEach(b=>b.disabled=false);setMode(mode);}}
$("btnKeyframe").addEventListener("click",genKeyframe);$("btnRegen").addEventListener("click",genKeyframe);

$("btnAnimate").addEventListener("click",async()=>{const btn=$("btnAnimate");$("anErr").textContent="";
  if(!lastKeyframeFile){$("anErr").textContent="请先生成关键帧";return;}
  if(!$("motion").value.trim()){$("anErr").textContent="请填写运动描述";return;}
  btn.disabled=true;btn.innerHTML='<span class="spin"></span>出片中…（真生成约几分钟）';
  try{const r=await fetch("/api/animate",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({keyframe_file:lastKeyframeFile,motion:$("motion").value,camera:$("camera").value,
      aspect,vid_model:$("vidModel").value,resolution,duration})});
    const d=await r.json();if(!r.ok)throw new Error(d.error||"出片失败");
    $("canvasVideo").src=d.video+"?t="+Date.now();$("canvasVideo").style.display="block";$("canvasImg").style.display="none";
    $("anCost").textContent="出片成本：$"+d.cost_usd+" · "+d.duration_s+"秒 · "+d.model;$("anLint").innerHTML=lintHtml(d.lint);renderBudget(d.budget);
  }catch(e){$("anErr").textContent=e.message;}finally{btn.disabled=false;refreshAnimBtn();}});

// 换场景
$("vdrop").addEventListener("click",()=>$("vfile").click());
$("vfile").addEventListener("change",async e=>{const f=e.target.files[0];if(!f)return;
  const fd=new FormData();fd.append("video",f);$("vdrop").textContent="上传中…";
  try{const r=await fetch("/api/upload_video",{method:"POST",body:fd});const d=await r.json();if(!r.ok)throw new Error(d.error);
    vidToken=d.ref;rVidDur=d.duration_s;$("vdrop").classList.add("on");$("vdrop").innerHTML="✓ 已上传（"+d.duration_s+"秒），点可换";
    refreshRestyle();
    $("rvideo").src=URL.createObjectURL(f);$("rvideo").style.display="block";$("rph").style.display="none";
  }catch(err){$("vdrop").textContent="上传失败："+err.message;}});

$("btnRestyle").addEventListener("click",async()=>{const btn=$("btnRestyle");$("rErr").textContent="";
  if(!vidToken){$("rErr").textContent="请先上传视频";return;}
  if(!$("rprompt").value.trim()){$("rErr").textContent="请描述要换成什么";return;}
  btn.disabled=true;btn.innerHTML='<span class="spin"></span>换场景中…（真生成约几分钟）';
  try{const r=await fetch("/api/restyle",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({ref:vidToken,prompt:$("rprompt").value,keep_audio:$("keepAudio").checked,
      model:$("rModel").value,trim:$("rTrim").checked})});
    const d=await r.json();if(!r.ok)throw new Error(d.error||"换场景失败");
    $("rvideo").src=d.video+"?t="+Date.now();$("rvideo").style.display="block";$("rph").style.display="none";
    $("rCost").textContent="成本：$"+d.cost_usd;renderBudget(d.budget);
  }catch(e){$("rErr").textContent=e.message;}finally{btn.disabled=false;setRestyleHint();}});

// 换脸：口播视频上传
$("fvdrop").addEventListener("click",()=>$("fvfile").click());
$("fvfile").addEventListener("change",async e=>{const f=e.target.files[0];if(!f)return;
  const fd=new FormData();fd.append("video",f);$("fvdrop").textContent="上传中…";
  try{const r=await fetch("/api/upload_video",{method:"POST",body:fd});const d=await r.json();if(!r.ok)throw new Error(d.error);
    fvidToken=d.ref;fVidDur=d.duration_s;$("fvdrop").classList.add("on");$("fvdrop").innerHTML="✓ 已上传（"+d.duration_s+"秒），点可换";
    refreshReface();
    $("fvideo").src=URL.createObjectURL(f);$("fvideo").style.display="block";$("fph").style.display="none";
  }catch(err){$("fvdrop").textContent="上传失败："+err.message;}});

// 换脸：目标人脸照片上传
$("fdrop").addEventListener("click",()=>$("ffile").click());
$("ffile").addEventListener("change",async e=>{const f=e.target.files[0];if(!f)return;
  const fd=new FormData();fd.append("photo",f);$("fdrop").textContent="上传中…";
  try{const r=await fetch("/api/upload",{method:"POST",body:fd});const d=await r.json();if(!r.ok)throw new Error(d.error);
    fFaceToken=d.ref;fFaceSlug="";[...$("fchips").children].forEach(x=>x.classList.remove("on"));
    $("fthumb").src=URL.createObjectURL(f);$("fthumb").style.display="block";
    $("fdrop").classList.add("on");$("fdrop").innerHTML="✓ 已上传目标脸，点可换";
  }catch(err){$("fdrop").textContent="上传失败："+err.message;}});

$("btnReface").addEventListener("click",async()=>{const btn=$("btnReface");$("fErr").textContent="";
  if(!fvidToken){$("fErr").textContent="请先上传口播视频";return;}
  const real=$("fModel").value!=="mock";
  if(real&&!fFaceToken&&!fFaceSlug&&!$("fprompt").value.trim()){
    $("fErr").textContent="真换脸需要上传目标人脸（或选已训角色），或用文字描述目标人";return;}
  btn.disabled=true;btn.innerHTML='<span class="spin"></span>换脸中…（真生成约几分钟）';
  try{const r=await fetch("/api/reface",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({ref:fvidToken,face_ref:fFaceToken,face_slug:fFaceSlug,
      prompt:$("fprompt").value,model:$("fModel").value,trim:$("fTrim").checked})});
    const d=await r.json();if(!r.ok)throw new Error(d.error||"换脸失败");
    $("fvideo").src=d.video+"?t="+Date.now();$("fvideo").style.display="block";$("fph").style.display="none";
    $("fCost").textContent="成本：$"+d.cost_usd;renderBudget(d.budget);
  }catch(e){$("fErr").textContent=e.message;}finally{btn.disabled=false;setRefaceHint();}});

// ✨ DeepSeek 提示词扩写（每个提示词框下方按钮）。运动按钮会带上所选运镜，按运镜生成。
[...document.querySelectorAll(".enh")].forEach(btn=>btn.addEventListener("click",async()=>{
  const ta=$(btn.dataset.t),raw=ta.value.trim();
  const cam=(btn.dataset.k==="motion"&&$("camera"))?$("camera").value:"";
  if(!raw&&!cam){ta.focus();ta.placeholder=btn.dataset.k==="motion"?"先选个运镜，或写一句怎么动…":"先写一句大白话，我来扩成详细指令…";return;}
  const old=btn.textContent;btn.disabled=true;btn.innerHTML='<span class="spin"></span>扩写中…';
  try{const r=await fetch("/api/enhance",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({raw,kind:btn.dataset.k,camera:cam})});
    const d=await r.json();if(!r.ok)throw new Error(d.error||"扩写失败");
    ta.value=d.prompt;ta.style.height="auto";ta.style.height=Math.min(ta.scrollHeight,260)+"px";
    btn.textContent="✓ 已扩写"+(d.camera?"（运镜："+d.camera+"）":"（"+d.model+"）");setTimeout(()=>btn.textContent=old,2800);
  }catch(e){btn.textContent="失败："+e.message;setTimeout(()=>btn.textContent=old,3000);}
  finally{btn.disabled=false;}}));

loadMeta();
</script></body></html>
"""

if __name__ == "__main__":
    print(f"[webui] 已加载密钥 {len(set(LOADED_KEYS))} 个 · http://127.0.0.1:5050", file=sys.stderr)
    app.run(host="127.0.0.1", port=5050, debug=False)
