#!/usr/bin/env python3
"""render — 纯函数：EDL(JSON) → FFmpeg → MP4。

两趟（Phase 0 求稳，不求快）：
  Pass 1  逐 clip 归一化(尺寸/帧率/SAR) + 调色(CDL 近似 + lut3d)，输出 .work/norm_i.mp4
  Pass 2  按 transition_in 用 xfade(画面)+acrossfade(声音) 组接成片

LLM 不参与这里——render 只消费 EDL，保证同输入同输出（可复现/可计费/可重跑）。

用法：
    python -m engine.render engine/.work/out.edl.json --out engine/.work/final.mp4
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from . import WORK_DIR, ENGINE_DIR
from . import edl as edl_mod


def run(cmd: list[str]) -> None:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        tail = "\n".join(p.stderr.strip().splitlines()[-12:])
        raise RuntimeError(f"FFmpeg 失败:\n$ {' '.join(cmd[:6])} …\n{tail}")


def has_audio(path: str) -> bool:
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
         "stream=index", "-of", "csv=p=0", path], capture_output=True, text=True, timeout=30)
    return bool(p.stdout.strip())


def probe_dur(path: str) -> float:
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, timeout=30)
    try:
        return float(p.stdout.strip())
    except ValueError:
        return 0.0


def filter_value(value: str) -> str:
    """Escape a value through FFmpeg's option parser, then filtergraph parser.

    This is not shell quoting: subprocess receives the graph as one argument.
    Keep POSIX filename backslashes; Path.as_posix() handles Windows separators.
    """
    def escape(text: str, special: str) -> str:
        return "".join("\\" + c if c in special else c for c in text)
    return escape(escape(value, "\\': \t\n"), "\\'[],; \t\n")


def color_chain(color: dict, fps: int, W: int, H: int, mode: str = "style") -> tuple[str, str]:
    """构造 pass1 的 video filter_complex（输入 [0:v]，输出 [outv]）。
    返回 (filter_complex 字符串, 人读说明)。

    调色标准（按 clip.grade.mode）：
      style    = 套这个风格的完整 CDL+LUT（生成镜头/平素材用）
      preserve = 只做尺寸/帧率归一化，不动颜色（已调好色的上传素材用，避免二次调色变诡异）
    """
    base = [
        f"fps={fps}",
        f"scale={W}:{H}:force_original_aspect_ratio=increase",
        f"crop={W}:{H}",
        "setsar=1",
    ]

    # preserve：保原色，只归一化格式
    if mode == "preserve":
        fc = f"[0:v]{','.join(base + ['format=yuv420p'])}[outv]"
        return fc, "preserve(保原色)"

    # style：套风格 CDL + 创意 LUT
    cdl = color.get("asc_cdl", {})
    slope = cdl.get("slope", [1.0, 1.0, 1.0])
    offset = cdl.get("offset", [0.0, 0.0, 0.0])
    power = cdl.get("power", [1.0, 1.0, 1.0])
    sat = float(cdl.get("saturation", 1.0))
    boff = round(sum(offset) / 3.0, 4)  # eq.brightness 是全局加项 → 用 offset 均值近似

    pre = base + [
        f"colorchannelmixer=rr={slope[0]}:gg={slope[1]}:bb={slope[2]}",
        f"eq=gamma_r={round(1/power[0],4)}:gamma_g={round(1/power[1],4)}:"
        f"gamma_b={round(1/power[2],4)}:brightness={boff}:saturation={sat}",
        "format=yuv420p",
    ]
    prechain = ",".join(pre)

    lut_ref = (color.get("creative_lut") or {}).get("ref")
    intensity = float((color.get("creative_lut") or {}).get("intensity", 1.0))
    lut_path = (ENGINE_DIR / lut_ref).resolve() if lut_ref else None

    if lut_path and lut_path.exists():
        cube = filter_value(lut_path.as_posix())
        if intensity < 0.999:
            k = round(intensity, 4)
            fc = (f"[0:v]{prechain}[g];[g]split=2[b][l];"
                  f"[l]lut3d=file={cube}:interp=tetrahedral[ld];"
                  f"[b][ld]blend=all_expr='A*(1-{k})+B*{k}'[outv]")
            note = f"CDL+LUT({lut_path.name}@{int(intensity*100)}%)"
        else:
            fc = f"[0:v]{prechain},lut3d=file={cube}:interp=tetrahedral[outv]"
            note = f"CDL+LUT({lut_path.name})"
    else:
        if lut_ref:
            print(f"⚠️  LUT 不存在，跳过: {lut_path}（先跑 engine/luts/make_luts.py）", file=sys.stderr)
        fc = f"[0:v]{prechain}[outv]"
        note = "CDL(无LUT)"
    return fc, note


def normalize_clip(clip: dict, color: dict, fps: int, W: int, H: int, out: Path,
                   pad_audio: bool = False) -> float:
    src = clip["source"]
    t_in = float(clip["in"])
    # Normalize the incoming handle too. Pass 2 discards only its video;
    # retaining the audio keeps B's source time identical after the picture cut.
    transition = clip.get("transition_in") or {}
    if transition.get("type") == "j-cut":
        t_in -= float(transition["duration"])
    dur = round(float(clip["out"]) - t_in, 3)
    mode = (clip.get("grade") or {}).get("mode", "style")  # 默认 style（向后兼容旧 EDL）
    fc, _ = color_chain(color, fps, W, H, mode)
    snd = has_audio(src)

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-ss", str(t_in), "-i", src]
    if not snd:
        cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]
    if pad_audio:
        cmd += ["-af", "apad"]
    cmd += ["-filter_complex", fc, "-map", "[outv]",
            "-map", "0:a:0" if snd else "1:a:0",
            "-t", str(dur), "-shortest",
            "-r", str(fps), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-ac", "2",
            str(out)]
    run(cmd)
    return probe_dur(str(out))


def assemble_j_cuts(norms: list[Path], clips: list[dict], fps: int, out: Path) -> None:
    """Assemble exact picture cuts with incoming audio handles (seconds).

    Trim AAC padding at every boundary. Legacy cut/dissolve overlaps remain
    unchanged when mixed with J-cuts; a J-cut never shortens the picture track.
    """
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    parts, lengths = [], []
    for i, (path, clip) in enumerate(zip(norms, clips)):
        cmd += ["-i", str(path)]
        t = clip.get("transition_in") or {}
        lead = float(t["duration"]) if t.get("type") == "j-cut" else 0.0
        length = edl_mod.clip_duration(clip)
        lengths.append(length)
        parts.append(f"[{i}:v]trim=start={lead}:duration={length},"
                     f"setpts=PTS-STARTPTS,fps={fps},settb=AVTB[v{i}]")
        parts.append(f"[{i}:a]apad,atrim=duration={length + lead},"
                     f"asetpts=PTS-STARTPTS[a{i}]")
    pv, pa, total = "v0", "a0", lengths[0]
    for i in range(1, len(norms)):
        t = clips[i].get("transition_in") or {}
        v, a = f"rawv{i}", f"rawa{i}"
        if t.get("type") == "j-cut":
            d = float(t["duration"])
            parts.append(f"[{pv}][v{i}]concat=n=2:v=1:a=0[{v}]")
            total += lengths[i]
        else:
            d = float(t["duration"]) if t.get("type") == "dissolve" else round(1 / fps, 4)
            parts.append(f"[{pv}][v{i}]xfade=transition=fade:duration={d}:"
                         f"offset={round(total - d, 4)}[{v}]")
            total += lengths[i] - d
        parts.append(f"[{pa}][a{i}]acrossfade=d={d}:c1=tri:c2=tri[{a}]")
        # xfade can emit an extra boundary frame (notably FFmpeg 4.4).
        # Bound every join, so subsequent J-cuts do not inherit that drift.
        frame_count = round(total * fps)
        total = frame_count / fps
        pv, pa = f"joinedv{i}", f"joineda{i}"
        parts.append(f"[{v}]trim=end_frame={frame_count},setpts=N/({fps}*TB),"
                     f"fps={fps},settb=AVTB[{pv}]")
        parts.append(f"[{a}]apad,atrim=duration={total},asetpts=PTS-STARTPTS[{pa}]")
    cmd += ["-filter_complex", ";".join(parts), "-map", f"[{pv}]", "-map", f"[{pa}]",
            "-r", str(fps), "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart", str(out)]
    run(cmd)


def assemble(norms: list[Path], durs: list[float], trans: list[dict],
             fps: int, out: Path) -> None:
    """Pass 2：xfade(画面)+acrossfade(声音) 链式组接。"""
    n = len(norms)
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for p in norms:
        cmd += ["-i", str(p)]

    if n == 1:
        cmd += ["-map", "0:v", "-map", "0:a"]
    else:
        parts = []
        # overlaps：dissolve 用转场时长；cut 用 1 帧（≈硬切，保持单一 xfade 链路）
        overlaps = [0.0]
        for i in range(1, n):
            t = trans[i]
            overlaps.append(t["duration"] if t.get("type") == "dissolve" else round(1.0 / fps, 4))

        prev_v, prev_a = "0:v", "0:a"
        cum = durs[0]
        for i in range(1, n):
            d = overlaps[i]
            off = round(cum - d, 4)
            tname = "fade" if trans[i].get("type") != "dissolve" else "fade"
            vlab, alab = f"vx{i}", f"ax{i}"
            parts.append(f"[{prev_v}][{i}:v]xfade=transition={tname}:duration={d}:offset={off}[{vlab}]")
            parts.append(f"[{prev_a}][{i}:a]acrossfade=d={d}:c1=tri:c2=tri[{alab}]")
            prev_v, prev_a = vlab, alab
            cum = round(cum + durs[i] - d, 4)
        cmd += ["-filter_complex", ";".join(parts), "-map", f"[{prev_v}]", "-map", f"[{prev_a}]"]

    cmd += ["-r", str(fps), "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart", str(out)]
    run(cmd)


def render_edl(edl, out_path, workdir=None, log=lambda m: None) -> Path:
    """纯函数：EDL(dict 或 json 路径) → 成片 MP4。CLI 与 backend 共用。"""
    if isinstance(edl, (str, Path)):
        edl = edl_mod.load(edl)
    errs = edl_mod.validate(edl)
    if errs:
        raise ValueError("EDL 非法: " + "; ".join(errs))

    r = edl["render"]
    W, H, fps = r["width"], r["height"], r["fps"]
    color = edl.get("color", {})
    clips = edl["clips"]
    j_cuts = any((c.get("transition_in") or {}).get("type") == "j-cut" for c in clips)
    # Reject impossible edits before creating intermediate files or output.
    if j_cuts:
        for i, c in enumerate(clips):
            if (c.get("transition_in") or {}).get("type") == "j-cut" and not has_audio(c["source"]):
                raise ValueError(f"clip[{i}] J-cut 需要后镜头有音轨；请改用 cut")
            if float(c["out"]) > probe_dur(c["source"]) + 1 / fps:
                raise ValueError(f"clip[{i}] out 超出素材时长")
    _, note = color_chain(color, fps, W, H)

    workdir = Path(workdir or (WORK_DIR / "norm"))
    workdir.mkdir(parents=True, exist_ok=True)
    log(f"调色标准 风格={note} | {W}x{H}@{fps} | {len(clips)} 镜头（按 clip 分级）")

    norms, durs, trans = [], [], []
    for i, c in enumerate(clips):
        out_i = workdir / f"norm_{i:03d}.mp4"
        actual = normalize_clip(c, color, fps, W, H, out_i, pad_audio=j_cuts)
        if j_cuts:
            # Container duration can be extended by a longer audio track. Check
            # actual decoded video length in the normalized MP4, too.
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                 "stream=duration", "-of", "csv=p=0", str(out_i)],
                capture_output=True, text=True, timeout=30, check=True)
            t = c.get("transition_in") or {}
            handle = float(t["duration"]) if t.get("type") == "j-cut" else 0.0
            expected = edl_mod.clip_duration(c) + handle
            if float(probe.stdout.strip()) < expected - 1e-4:
                raise ValueError(f"clip[{i}] 视频不足以覆盖 in/out 与 J-cut 余量")
        gmode = (c.get("grade") or {}).get("mode", "style")
        norms.append(out_i)
        durs.append(actual)
        trans.append(c.get("transition_in", {"type": "cut", "duration": 0.0}))
        log(f"[{i+1}/{len(clips)}] {c['origin']:9s} {c.get('role',''):6s} "
            f"grade={gmode:8s} {actual:.2f}s ▸ {Path(c['source']).name}")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if j_cuts:
        assemble_j_cuts(norms, clips, fps, out_path)
    else:
        assemble(norms, durs, trans, fps, out_path)
    total = probe_dur(str(out_path))
    log(f"成片 {out_path.name} ({total:.1f}s)")
    return out_path


def main():
    ap = argparse.ArgumentParser(description="Open Edit — render (EDL→MP4 纯函数渲染)")
    ap.add_argument("edl", help="EDL JSON 路径")
    ap.add_argument("--out", default=str(WORK_DIR / "final.mp4"), help="成片输出 MP4")
    ap.add_argument("--workdir", default=str(WORK_DIR / "norm"), help="中间归一化产物目录")
    args = ap.parse_args()

    def log(m):
        print("   " + m, file=sys.stderr)

    try:
        out = render_edl(args.edl, args.out, args.workdir, log=log)
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    print(str(out))


if __name__ == "__main__":
    main()
