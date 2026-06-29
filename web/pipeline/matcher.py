"""Match video analysis results against the Open Edit style taxonomy"""
import os
import re
import yaml
from pathlib import Path


def load_all_styles(taxonomy_dir: str) -> list[dict]:
    """Load all style files from taxonomy directory."""
    styles = []
    base = Path(taxonomy_dir)
    if not base.exists():
        return styles

    for subdir in ["custom-analysis", "from-shotdeck"]:
        d = base / subdir
        if not d.exists():
            continue
        for f in sorted(d.glob("*.md")):
            if f.name == "_template.md":
                continue
            meta = parse_style_frontmatter(f)
            if meta:
                styles.append(meta)
    return styles


def parse_style_frontmatter(filepath: Path) -> dict | None:
    """Parse YAML frontmatter and extract key parameters from a style file."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except:
        return None

    if not content.startswith("---"):
        return None

    end = content.find("\n---", 3)
    if end == -1:
        return None

    yaml_text = content[3:end]
    try:
        meta = yaml.safe_load(yaml_text)
    except:
        meta = {}

    if not meta or not meta.get("name"):
        return None

    # Extract Layer 2 parameters
    body = content[end + 4:]
    params = extract_layer2_params(body)

    return {
        "name": meta.get("name", ""),
        "description": meta.get("description", ""),
        "category": meta.get("category", ""),
        "triggers": meta.get("triggers", []),
        "subcategory": meta.get("subcategory", ""),
        "source": meta.get("source", {}),
        "params": params,
    }


def extract_layer2_params(body: str) -> dict:
    """Extract Layer 2 (parameter layer) values from style markdown."""
    params = {}

    # Find Layer 2 section
    layer2_match = re.search(r'## Layer 2[:\s](.*?)(?=## Layer 3|## |\Z)', body, re.DOTALL)
    if not layer2_match:
        return params

    layer2_text = layer2_match.group(1)

    # Color temperature
    m = re.search(r'(暖|冷|中性)[色调温]*', layer2_text)
    if m:
        temp_map = {"暖": "warm", "冷": "cool", "中性": "neutral"}
        params["color_tone"] = temp_map.get(m.group(1), m.group(1))

    # Color temp range
    m = re.search(r'(\d{3,5})\s*[–\-~]\s*(\d{3,5})\s*K', layer2_text)
    if m:
        params["color_temp"] = f"{m.group(1)}-{m.group(2)}K"

    # Saturation
    m = re.search(r'saturation[:\s]*(-?\d+)%?', layer2_text, re.IGNORECASE)
    if m:
        params["saturation"] = int(m.group(1))

    # Contrast
    m = re.search(r'contrast[:\s]*(-?\d+)%?', layer2_text, re.IGNORECASE)
    if m:
        params["contrast"] = int(m.group(1))

    # Shot duration
    m = re.search(r'avg[.\s]*shot[.\s]*dur[.\s]*(\d+\.?\d*)', layer2_text, re.IGNORECASE)
    if m:
        params["avg_shot_duration"] = float(m.group(1))

    # Aspect ratio
    m = re.search(r'(9:16|16:9|1:1|4:3)', layer2_text)
    if m:
        params["aspect_ratio"] = m.group(1)

    # Hard cut percentage
    m = re.search(r'hard[.\s]*cut.*?(\d+)%', layer2_text, re.IGNORECASE)
    if m:
        params["hard_cut_pct"] = int(m.group(1))

    # Lighting keywords
    lighting_keywords = ["golden hour", "natural light", "studio", "soft", "hard", "low key", "high key"]
    for kw in lighting_keywords:
        if kw.lower() in layer2_text.lower():
            params.setdefault("lighting_keywords", []).append(kw)

    return params


def match_style(analysis: dict, styles: list[dict]) -> list[dict]:
    """Find best matching styles for the analyzed video."""
    if not analysis or not styles:
        return []

    scores = []
    for style in styles:
        score = 0
        matches = []

        # Color tone matching
        video_tone = analysis.get("color_tone", {}).get("dominant", "")
        style_tone = style.get("params", {}).get("color_tone", "")
        if video_tone and style_tone and video_tone == style_tone:
            score += 25
            matches.append(f"color_tone:{video_tone}")

        # Lighting matching
        video_lighting = analysis.get("lighting", {}).get("dominant", "")
        style_lighting = style.get("params", {}).get("lighting_keywords", [])
        if video_lighting and style_lighting:
            for sl in style_lighting:
                if sl.split()[-1].lower() in video_lighting.lower():
                    score += 15
                    matches.append(f"lighting:{sl}")

        # Shot type matching
        video_shot = analysis.get("shot_type", {}).get("dominant", "")
        if video_shot == "closeup" or video_shot == "extreme-closeup":
            # If style has short avg shot duration, likely uses lots of closeups
            avg_shot = style.get("params", {}).get("avg_shot_duration", 3)
            if avg_shot < 2.0:
                score += 10
                matches.append("fast_cuts")

        # Mood matching
        video_mood = analysis.get("mood", {}).get("dominant", "")
        if video_mood:
            # Check if description mentions mood
            desc = style.get("description", "").lower()
            mood_words = {
                "cozy": ["warm", "cozy", "intimate", "soft"],
                "dramatic": ["dramatic", "cinematic", "high contrast", "bold"],
                "peaceful": ["peaceful", "calm", "slow", "serene"],
                "energetic": ["energetic", "fast", "dynamic", "vibrant"],
                "nostalgic": ["nostalgic", "vintage", "retro", "film grain", "faded"],
            }
            words = mood_words.get(video_mood, [])
            for w in words:
                if w in desc:
                    score += 10
                    matches.append(f"mood:{w}")
                    break

        # Trigger matching
        if style.get("triggers"):
            for trigger in style["triggers"]:
                t_lower = trigger.lower()
                desc = style.get("description", "").lower()
                if t_lower in desc:
                    score += 5
                    matches.append(f"trigger:{trigger}")

        scores.append({
            "style_name": style["name"],
            "description": style["description"][:200] if style.get("description") else "",
            "score": score,
            "matches": matches,
            "subcategory": style.get("subcategory", ""),
            "source_creator": style.get("source", {}).get("creator", ""),
        })

    # Sort by score descending
    scores.sort(key=lambda x: -x["score"])
    return scores[:5]
