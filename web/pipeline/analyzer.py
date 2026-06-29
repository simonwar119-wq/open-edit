"""AI-powered frame analysis using Doubao ARK API"""
import base64
import json
import os
import re
from http.client import HTTPSConnection


VISION_PROMPT = """Analyze this video frame and provide a JSON response with these fields:
{
  "shot_type": "wide/medium/closeup/extreme-closeup/detail",
  "composition": "centered/rule-of-thirds/leading-lines/frame-within-frame/symmetry/asymmetric/negative-space",
  "lighting": "natural/golden-hour/studio/high-contrast/soft/flat/backlit/silhouette",
  "color_tone": "warm/cool/neutral/muted/vibrant/monochrome/teal-orange/sepia",
  "mood": "cozy/dramatic/mysterious/energetic/peaceful/nostalgic/intimate/epic",
  "camera_movement_inferred": "static/panning/tilting/tracking/handheld/steadicam/zoom/dolly",
  "depth": "shallow/medium/deep",
  "dominant_colors": ["#hex1", "#hex2", "#hex3"],
  "scene_description": "One sentence describing what's in the frame",
  "estimated_aperture": "wide/medium/narrow",
  "contrast_level": "low/medium/high"
}
Return ONLY valid JSON, no other text."""


def analyze_frame_with_doubao(image_path: str, api_key: str, model: str = "doubao-seed-2-0-lite-260215") -> dict | None:
    """Analyze a single frame using Doubao ARK API (OpenAI-compatible)."""
    if not api_key:
        return None

    try:
        with open(image_path, "rb") as f:
            # Resize large images first to save tokens
            image_data = base64.b64encode(f.read()).decode("utf-8")

        payload = json.dumps({
            "model": model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                    {"type": "text", "text": VISION_PROMPT}
                ]
            }],
            "max_tokens": 1000
        })

        conn = HTTPSConnection("ark.cn-beijing.volces.com", timeout=30)
        conn.request("POST", "/api/v3/chat/completions", payload, {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })
        resp = conn.getresponse()
        body = resp.read().decode("utf-8")
        conn.close()

        data = json.loads(body)
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
            return result

        return {"error": "No JSON found in response", "raw": content[:200]}

    except Exception as e:
        return {"error": str(e)}
