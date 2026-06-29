#!/usr/bin/env python3
"""ShotDeck auto-collector v2 - Edgar Wright"""
import json, re, time, sys, os
from datetime import datetime
from urllib.request import Request, urlopen

BRIDGE_URL = "http://127.0.0.1:8642/action"
DATAFILE = os.path.expanduser("~/Desktop/Agent/open-edit/taxonomy/03-styles/from-shotdeck/edgar-wright/shotdeck-data.jsonl")
LOGFILE = os.path.expanduser("~/Desktop/Agent/shotdeck_poller.log")
POLL_INTERVAL = 3

def bridge(action, params=None):
    payload = json.dumps({"action": action, "params": params or {}}).encode()
    try:
        resp = urlopen(Request(BRIDGE_URL, data=payload, headers={"Content-Type": "application/json"}), timeout=10)
        return json.loads(resp.read())
    except Exception as e:
        return None

def extract_shot_meta(text):
    lines = text.split("\n")
    shot_title = None
    for i, line in enumerate(lines):
        m = re.match(r"^([A-Z][A-Z0-9\s\-\.'\"\,\!\?\&\:\(\)]+)\s*\((\d{4})\)", line.strip())
        if m and i > 15:
            shot_title = f"{m.group(1).strip()} ({m.group(2)})"
            break
    
    if not shot_title:
        return None
    
    meta = {"title": shot_title, "captured_at": datetime.now().isoformat()}
    start = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if shot_title.split("(")[0].strip() in stripped and "(" in stripped and ")" in stripped:
            start = i
            break
    
    if start is None:
        return {"title": shot_title, "captured_at": datetime.now().isoformat()}
    
    field, vals = None, []
    for j in range(start + 1, len(lines)):
        l = lines[j].strip()
        if "SIMILAR SHOTS" in l or "SEE MORE" in l:
            if field and vals:
                meta[field.lower().replace(" ", "_")] = " ".join(vals).strip()
            break
        fm = re.match(r"^([A-Z][A-Z\s/]+):\s*$", l)
        if fm:
            if field and vals:
                meta[field.lower().replace(" ", "_")] = " ".join(vals).strip()
            field = fm.group(1).strip()
            vals = []
            continue
        if field and l:
            vals.append(l)
    if field and vals:
        meta[field.lower().replace(" ", "_")] = " ".join(vals).strip()
    
    return meta

# === Main Loop ===
count = 0
if os.path.exists(DATAFILE):
    with open(DATAFILE) as f:
        for line in f:
            if line.strip():
                count += 1

with open(LOGFILE, "a") as f:
    f.write(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Edgar Wright poller started (existing: {count})\n")

last_shot = None
while True:
    time.sleep(POLL_INTERVAL)
    bridge("inject")
    time.sleep(0.5)
    
    result = bridge("read")
    if not result or result.get("status") != "ok":
        continue
    
    text = result.get("data", {}).get("text", "")
    if not text or len(text) < 500:
        continue
    
    meta = extract_shot_meta(text)
    if not meta:
        continue
    
    if meta["title"] == last_shot:
        continue
    
    last_shot = meta["title"]
    count += 1
    
    with open(DATAFILE, "a") as f:
        f.write(json.dumps(meta, ensure_ascii=False) + "\n")
    
    st = meta.get("shot_type", "?")
    fs = meta.get("frame_size", "?")
    comp = meta.get("composition", "?")
    ar = meta.get("aspect_ratio", "?")
    col = meta.get("color", "?")
    mov = meta.get("camera_movement", "")
    
    with open(LOGFILE, "a") as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ #{count} {meta['title'][:50]} | {st} | {fs} | {comp} | {ar} | {col}\n")
