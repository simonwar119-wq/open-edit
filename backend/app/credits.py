"""积分账本：reserve（烧钱前 gate）→ spend（按实际）→ settle（结算）。

plan 的成本红线：生成厂商调用 = COGS 主体。烧钱前先按预算 gate；
每次生成按实际 debit；自有账本(Postgres/SQLite) 为真源，生产再镜像到 Stripe meter。
"""

from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .models import CreditLedger, GenerationRequest


class InsufficientCredits(Exception):
    pass


def balance(session: Session, org_id: str) -> float:
    total = session.execute(
        select(func.coalesce(func.sum(CreditLedger.amount_usd), 0.0))
        .where(CreditLedger.org_id == org_id)
    ).scalar_one()
    return round(float(total), 4)


def topup(session: Session, org_id: str, amount_usd: float, note: str = "topup") -> float:
    session.add(CreditLedger(org_id=org_id, kind="topup", amount_usd=abs(amount_usd), note=note))
    session.commit()
    return balance(session, org_id)


def reserve(session: Session, org_id: str, est_usd: float) -> None:
    """烧钱前 gate：余额不足直接拒绝（不写 ledger，仅校验）。"""
    bal = balance(session, org_id)
    if est_usd > bal + 1e-6:
        raise InsufficientCredits(f"余额不足：需预留 ${est_usd:.2f}，当前 ${bal:.2f}")


def spend(session: Session, org_id: str, job_id: str, amount_usd: float,
          provider: str, model: str, prompt: str = "", commercial_ok: bool = True) -> None:
    """记一次真实生成花费 + 一条 generation_request。"""
    if amount_usd > 0:
        session.add(CreditLedger(org_id=org_id, job_id=job_id, kind="spend",
                                 amount_usd=-abs(amount_usd), note=f"{provider}/{model}"))
    session.add(GenerationRequest(job_id=job_id, provider=provider, model=model,
                                  cost_usd=amount_usd, commercial_ok=1 if commercial_ok else 0,
                                  prompt=prompt))
    session.commit()


def settle_from_edl(session: Session, org_id: str, job_id: str, edl: dict) -> float:
    """从 EDL 的每个 generated clip 记账（post-hoc，dev 简化）。返回本 job 总花费。"""
    total = 0.0
    for c in edl.get("clips", []):
        g = c.get("gen")
        if not g:
            continue
        cost = float(g.get("cost_usd", 0.0))
        total += cost
        spend(session, org_id, job_id, cost, g.get("provider", "?"),
              g.get("model", "?"), g.get("prompt", ""), bool(g.get("commercial_ok", True)))
    return round(total, 4)
