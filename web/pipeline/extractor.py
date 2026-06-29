"""FFmpeg-based video analysis and frame extraction"""
import json
import os
import subprocess
from pathlib import Path

# Config defaults
FRAME_INTERVAL = 5
SAMPLE_FRAMES = 12


def get_video_info(video_path: str) -> dict:
    """Extract video metadata using ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams",
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    data = json.loads(result.stdout)

    video_stream = None
    audio_stream = None
    for stream in data.get("streams", []):
        if stream["codec_type"] == "video":
            video_stream = stream
        elif stream["codec_type"] == "audio":
            audio_stream = stream

    info = {
        "duration_s": 0,
        "width": 0,
        "height": 0,
        "fps": 0,
        "bitrate_kbps": 0,
        "codec": "",
        "has_audio": False,
    }

    if video_stream:
        info["width"] = int(video_stream.get("width", 0))
        info["height"] = int(video_stream.get("height", 0))
        fps_str = video_stream.get("r_frame_rate", "0/1")
        if "/" in fps_str:
            num, den = fps_str.split("/")
            info["fps"] = round(float(num) / float(den), 1) if float(den) > 0 else 0
        info["codec"] = video_stream.get("codec_name", "")
        info["bitrate_kbps"] = round(int(video_stream.get("bit_rate", 0)) / 1000)

    if audio_stream:
        info["has_audio"] = True

    # Format-level duration (more reliable)
    fmt = data.get("format", {})
    dur = fmt.get("duration", "0")
    info["duration_s"] = round(float(dur), 1)

    return info


def extract_frames(video_path: str, output_dir: str,
                   interval: int = None, max_frames: int = None) -> list[str]:
    """Extract key frames at regular intervals from video.

    Returns list of frame file paths.
    """
    if interval is None:
        interval = FRAME_INTERVAL
    if max_frames is None:
        max_frames = SAMPLE_FRAMES

    info = get_video_info(video_path)
    duration = info["duration_s"]

    # Calculate timestamps
    timestamps = []
    for t in range(0, int(duration), interval):
        timestamps.append(t)
        if len(timestamps) >= max_frames:
            break

    # Also add the last frame if not included
    if timestamps and timestamps[-1] < int(duration) - 1:
        timestamps.append(int(duration) - 1)

    frame_paths = []
    for i, ts in enumerate(timestamps):
        out_path = os.path.join(output_dir, f"frame_{i:03d}.jpg")
        cmd = [
            "ffmpeg", "-ss", str(ts),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            "-vf", "scale='min(1920,iw)':min(1080,ih):force_original_aspect_ratio=decrease",
            "-y", out_path
        ]
        subprocess.run(cmd, capture_output=True, timeout=15)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            frame_paths.append((ts, out_path))

    return frame_paths


def analyze_rhythm(video_path: str) -> dict:
    """Analyze video rhythm: scene changes, motion, average shot length."""
    info = get_video_info(video_path)
    duration = info["duration_s"]
    fps = info["fps"]

    if fps == 0 or duration == 0:
        return {"avg_shot_duration": 0, "scene_changes": 0, "motion_score": 0}

    # Detect scene changes using ffmpeg scene detection
    cmd = [
        "ffprobe", "-v", "quiet",
        "-show_frames",
        "-of", "compact=p=0",
        "-f", "lavfi",
        f"movie={video_path},select='gt(scene,0.3)'",
        video_path
    ]

    scene_changes = 0
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        scene_changes = len([l for l in result.stdout.split("\n") if l.strip()])
    except:
        pass

    avg_shot = round(duration / max(scene_changes, 1), 1) if scene_changes > 0 else duration

    # Motion score: rough estimate based on bitrate and resolution
    motion_score = "low"
    if info["bitrate_kbps"] > 20000:
        motion_score = "high"
    elif info["bitrate_kbps"] > 8000:
        motion_score = "medium"

    return {
        "duration_s": duration,
        "fps": fps,
        "scene_changes": scene_changes,
        "avg_shot_duration_s": avg_shot,
        "estimated_shots": max(scene_changes, 1),
        "motion_level": motion_score,
        "resolution": f"{info['width']}x{info['height']}",
        "codec": info["codec"],
        "bitrate_kbps": info["bitrate_kbps"],
        "has_audio": info["has_audio"],
    }
