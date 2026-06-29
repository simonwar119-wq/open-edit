"""Main analysis pipeline: video in → report out"""
import json
import os
import shutil
import tempfile
import time
from pathlib import Path

from . import extractor
from . import analyzer
from . import matcher


def analyze_video(video_path: str, api_key: str, taxonomy_dir: str,
                  delete_after: bool = True) -> dict:
    """Run the full analysis pipeline on a video file.

    Returns a structured report dict.
    """
    start_time = time.time()
    result = {
        "video": {},
        "rhythm": {},
        "frames": {"count": 0},
        "visual_analysis": {},
        "style_matches": [],
        "processing_time_s": 0,
        "error": None,
    }

    # Create temp dir for frames
    temp_dir = tempfile.mkdtemp(prefix="open_edit_")

    try:
        # Step 1: Extract video info and rhythm
        result["video"] = extractor.get_video_info(video_path)
        result["rhythm"] = extractor.analyze_rhythm(video_path)

        # Step 2: Extract frames
        frames = extractor.extract_frames(video_path, temp_dir)
        result["frames"]["count"] = len(frames)
        result["frames"]["interval_s"] = min(
            extractor.FRAME_INTERVAL,
            result["video"].get("duration_s", 60) // max(len(frames), 1)
        )

        # Step 3: Analyze frames with Vision API
        frame_analyses = []
        for ts, frame_path in frames:
            analysis = analyzer.analyze_frame_with_doubao(frame_path, api_key)
            if analysis:
                analysis["timestamp_s"] = ts
                frame_analyses.append(analysis)

        # Step 4: Aggregate frame analyses
        result["visual_analysis"] = analyzer.aggregate_frame_analyses(frame_analyses)

        # Step 5: Match against style taxonomy
        styles = matcher.load_all_styles(taxonomy_dir)
        result["style_matches"] = matcher.match_style(
            result["visual_analysis"], styles
        )

        # Step 6: Generate analysis summary
        result["summary"] = generate_summary(result)

    except Exception as e:
        result["error"] = str(e)

    finally:
        # Cleanup temp dir
        shutil.rmtree(temp_dir, ignore_errors=True)

        # Delete original video if requested
        if delete_after and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except:
                pass

    result["processing_time_s"] = round(time.time() - start_time, 1)
    return result


def generate_summary(result: dict) -> str:
    """Generate a human-readable summary paragraph."""
    va = result.get("visual_analysis", {})
    rhythm = result.get("rhythm", {})
    matches = result.get("style_matches", [])

    parts = []

    # Color bias
    bias = va.get("overall_color_bias", "")
    if bias:
        bias_labels = {"warm": "暖色调", "cool": "冷色调", "neutral": "中性调", "mixed": "混合色调"}
        parts.append(f"整体偏{bias_labels.get(bias, bias)}")

    # Shot type
    shot = va.get("shot_type", {}).get("dominant", "")
    if shot:
        shot_labels = {
            "wide": "以全景/远景为主", "medium": "以中景为主",
            "closeup": "以特写为主", "extreme-closeup": "以大特写为主"
        }
        parts.append(shot_labels.get(shot, f"以{shot}为主"))

    # Lighting
    light = va.get("lighting", {}).get("dominant", "")
    if light:
        parts.append(f"光源以{light}为主")

    # Rhythm
    avg_shot = rhythm.get("avg_shot_duration_s", 0)
    if avg_shot > 0:
        if avg_shot < 2:
            rhythm_desc = "快节奏 (平均镜头<2s)"
        elif avg_shot < 4:
            rhythm_desc = "中等节奏 (平均镜头2-4s)"
        else:
            rhythm_desc = "慢节奏 (平均镜头>4s)"
        parts.append(rhythm_desc)

    # Style match
    if matches and matches[0]["score"] > 20:
        top = matches[0]
        parts.append(f"风格接近「{top['style_name']}」(匹配度{top['score']}%)")

    if not parts:
        return "视频分析完成。"

    return "，".join(parts) + "。"
