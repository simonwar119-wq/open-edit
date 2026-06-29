#!/usr/bin/env python3
"""ShotDeck auto-collector - Wong Kar-wai"""
import json, re, time, os
from datetime import datetime
from urllib.request import Request, urlopen

BRIDGE_URL = "http://127.0.0.1:8642/action"
DATAFILE = os.path.expanduser("~/Desktop/Agent/open-edit/taxonomy/03-styles/from-shotdeck/wong-kar-wai/shotdeck-data.jsonl")
LOGFILE = os.path.expanduser("~/Desktop/Agent/shotdeck_poller.log")
POLL_INTERVAL = 3

def bridge(a, p=None):
    payload = json.dumps({"action": a, "params": p or {}}).encode()
    try:
        return json.loads(urlopen(Request(BRIDGE_URL, data=payload, headers={"Content-Type":"application/json"}), timeout=10).read())
    except: return None

def extract(text):
    lines = text.split("\n")
    for i, l in enumerate(lines):
        m = re.match(r"^([A-Z][A-Z0-9\s\-\.'\"\,\!\?\&\:\(\)]+)\s*\((\d{4})\)", l.strip())
        if m and i > 15:
            title = f"{m.group(1).strip()} ({m.group(2)})"
            meta = {"title": title, "captured_at": datetime.now().isoformat()}
            start = next((j for j, l2 in enumerate(lines) if title.split("(")[0].strip() in l2.strip() and "(" in l2 and ")" in l2), None)
            if start:
                f, v = None, []
                for j in range(start+1, len(lines)):
                    l = lines[j].strip()
                    if "SIMILAR" in l or "SEE MORE" in l:
                        if f and v: meta[f.lower().replace(" ","_")] = " ".join(v).strip()
                        break
                    fm = re.match(r"^([A-Z][A-Z\s/]+):\s*$", l)
                    if fm:
                        if f and v: meta[f.lower().replace(" ","_")] = " ".join(v).strip()
                        f, v = fm.group(1).strip(), []
                        continue
                    if f and l: v.append(l)
                if f and v: meta[f.lower().replace(" ","_")] = " ".join(v).strip()
            return meta

count = 0
if os.path.exists(DATAFILE):
    with open(DATAFILE) as f:
        for line in f:
            if line.strip(): count += 1

with open(LOGFILE, "a") as f:
    f.write(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Wong Kar-wai poller started (existing: {count})\n")

last = None
while True:
    time.sleep(POLL_INTERVAL)
    bridge("inject")
    time.sleep(0.5)
    r = bridge("read")
    if not r or r.get("status") != "ok": continue
    t = r.get("data",{}).get("text","")
    if not t or len(t) < 500: continue
    m = extract(t)
    if not m or m["title"] == last: continue
    last = m["title"]; count += 1
    with open(DATAFILE, "a") as f:
        f.write(json.dumps(m, ensure_ascii=False) + "\n")
    with open(LOGFILE, "a") as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ #{count} {m['title'][:50]} | {m.get('shot_type','?')} | {m.get('frame_size','?')} | {m.get('composition','?')} | {m.get('aspect_ratio','?')} | {m.get('color','?')}\n")
