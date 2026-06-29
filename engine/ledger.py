"""ledger — open-edit 生成台账（抄自 Higgsfield higgsfield_memory.py 思路）。

把"彩票税"工程化：每次生成记一行（kept/rejected/flagged + 成本 + 镜头类型），
攒 30-40 样本后算每类镜头的真实 keeper rate（takes-per-kept）与累计成本，
并自动判 iterate（系统性失误，改 prompt）vs batch（随机性方差，锁 prompt 跑 N 个挑）。

append-only JSONL，存 engine/.work/ledger/<project>.jsonl。CLI：
    python -m engine.ledger log <project> --shot hero_walk --status kept --cost 1.5 --model seedance-2.0
    python -m engine.ledger ratio <project>
    python -m engine.ledger budget <project>
"""
from __future__ import annotations

import json
import sys
import argparse
from pathlib import Path

from engine import WORK_DIR

LEDGER_DIR = WORK_DIR / "ledger"
LEDGER_DIR.mkdir(parents=True, exist_ok=True)

STATUSES = ("kept", "rejected", "flagged")


def _path(project: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in project)
    return LEDGER_DIR / f"{safe}.jsonl"


def log_gen(project: str, *, shot: str, status: str, cost_usd: float = 0.0,
            model: str = "", reject_reason: str = "", ts: str = "") -> dict:
    """记一行生成。status ∈ kept/rejected/flagged。ts 由调用方传入（本环境无 Date.now）。"""
    if status not in STATUSES:
        raise ValueError(f"status 必须是 {STATUSES}")
    row = {"shot": shot, "status": status, "cost_usd": round(float(cost_usd), 4),
           "model": model, "reject_reason": reject_reason, "ts": ts}
    with _path(project).open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def _read(project: str) -> list[dict]:
    p = _path(project)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def ratio(project: str) -> dict:
    """每类镜头的 takes-per-kept（keeper rate）。"""
    rows = _read(project)
    by_shot: dict[str, dict] = {}
    for r in rows:
        s = by_shot.setdefault(r["shot"], {"total": 0, "kept": 0, "cost": 0.0})
        s["total"] += 1
        s["cost"] += r.get("cost_usd", 0.0)
        if r["status"] == "kept":
            s["kept"] += 1
    out = {}
    for shot, s in by_shot.items():
        keep_rate = s["kept"] / s["total"] if s["total"] else 0.0
        out[shot] = {
            "total": s["total"], "kept": s["kept"],
            "keep_rate": round(keep_rate, 3),
            "takes_per_kept": round(s["total"] / s["kept"], 2) if s["kept"] else None,
            "cost_total_usd": round(s["cost"], 2),
            "cost_per_kept_usd": round(s["cost"] / s["kept"], 2) if s["kept"] else None,
        }
    return out


def budget(project: str) -> dict:
    rows = _read(project)
    spent = round(sum(r.get("cost_usd", 0.0) for r in rows), 2)
    kept = sum(1 for r in rows if r["status"] == "kept")
    return {"generations": len(rows), "kept": kept, "spent_usd": spent,
            "overall_keep_rate": round(kept / len(rows), 3) if rows else 0.0,
            "cost_per_kept_usd": round(spent / kept, 2) if kept else None}


def fork_verdict(project: str, shot: str, min_samples: int = 4) -> dict:
    """iterate vs batch：同一镜头若拒因高度集中（同样地方崩）→ 系统性 → iterate（改 prompt）；
    若拒因分散 → 随机方差 → batch（锁 prompt 跑 N 个挑最优）。"""
    rows = [r for r in _read(project) if r["shot"] == shot]
    if len(rows) < min_samples:
        return {"verdict": "insufficient_data", "samples": len(rows)}
    reasons = [r.get("reject_reason", "").strip().lower() for r in rows if r["status"] != "kept"]
    reasons = [x for x in reasons if x]
    if not reasons:
        return {"verdict": "healthy", "samples": len(rows)}
    top = max(set(reasons), key=reasons.count)
    concentration = reasons.count(top) / len(reasons)
    verdict = "iterate" if concentration >= 0.5 else "batch"
    return {"verdict": verdict, "samples": len(rows), "dominant_reject": top,
            "concentration": round(concentration, 2),
            "hint": ("同一处反复崩=系统性，改 prompt 那一项" if verdict == "iterate"
                     else "拒因分散=随机方差，锁 prompt 批量跑挑最优")}


def _main():
    ap = argparse.ArgumentParser(prog="ledger")
    sub = ap.add_subparsers(dest="cmd", required=True)
    pl = sub.add_parser("log"); pl.add_argument("project"); pl.add_argument("--shot", required=True)
    pl.add_argument("--status", required=True, choices=STATUSES); pl.add_argument("--cost", type=float, default=0.0)
    pl.add_argument("--model", default=""); pl.add_argument("--reason", default=""); pl.add_argument("--ts", default="")
    for name in ("ratio", "budget"):
        sp = sub.add_parser(name); sp.add_argument("project")
    pf = sub.add_parser("fork"); pf.add_argument("project"); pf.add_argument("--shot", required=True)
    a = ap.parse_args()
    if a.cmd == "log":
        out = log_gen(a.project, shot=a.shot, status=a.status, cost_usd=a.cost, model=a.model,
                      reject_reason=a.reason, ts=a.ts)
    elif a.cmd == "ratio":
        out = ratio(a.project)
    elif a.cmd == "budget":
        out = budget(a.project)
    else:
        out = fork_verdict(a.project, a.shot)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _main()
