#!/usr/bin/env python3
"""Open Edit — Video Style Analyzer Web App"""
import os
import uuid
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from pipeline import analyze_video

app = Flask(__name__)
app.config.from_pyfile("config.py")

# Ensure upload dir exists
os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)

# Home page
@app.route("/")
def index():
    return render_template("index.html")

# Upload endpoint
@app.route("/analyze", methods=["POST"])
def upload_and_analyze():
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    file = request.files["video"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in app.config["ALLOWED_EXTENSIONS"]:
        return jsonify({"error": f"Unsupported format: {ext}. Allowed: {', '.join(app.config['ALLOWED_EXTENSIONS'])}"}), 400

    # Save uploaded file
    session_id = uuid.uuid4().hex[:12]
    safe_name = f"{session_id}{ext}"
    video_path = os.path.join(app.config["UPLOAD_DIR"], safe_name)
    file.save(video_path)

    # Validate file size
    file_size = os.path.getsize(video_path)
    max_bytes = app.config["MAX_UPLOAD_SIZE_MB"] * 1024 * 1024
    if file_size > max_bytes:
        os.remove(video_path)
        return jsonify({"error": f"File too large. Max: {app.config['MAX_UPLOAD_SIZE_MB']}MB"}), 400

    # Get API key (from config or env)
    api_key = app.config.get("ARK_API_KEY", os.environ.get("ARK_API_KEY", ""))
    if not api_key:
        os.remove(video_path)
        return jsonify({"error": "Server not configured with Vision API key"}), 500

    # Run analysis
    try:
        result = analyze_video(
            video_path=video_path,
            api_key=api_key,
            taxonomy_dir=app.config["TAXONOMY_DIR"],
            delete_after=True,
        )
        return jsonify(result)
    except Exception as e:
        # Cleanup on error
        if os.path.exists(video_path):
            os.remove(video_path)
        return jsonify({"error": str(e)}), 500

# Serve static files
@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)

# Check ARK_API_KEY
API_KEY = app.config.get("ARK_API_KEY") or os.environ.get("ARK_API_KEY", "")

if __name__ == "__main__":
    if not API_KEY:
        print("⚠️  WARNING: ARK_API_KEY not set. Vision analysis will fail.")
    print(f"🚀 Open Edit running on http://{app.config['HOST']}:{app.config['PORT']}")
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])
