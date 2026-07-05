"""
L1 of the TASA knowledge model: dynamic per-KC mastery.

Mastery is a Bayesian Knowledge Tracing (BKT) posterior that updates on every
graded attempt, and a forgetting curve decays it between attempts. Together they
replace the old static 0-100 skill score with a calibrated, time-aware
probability. See docs/tasa-knowledge-model.md.
"""
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.models import KCMastery, KnowledgeComponent
from app.services.kc_mapping import resolve_kcs

# A grade at/above this fraction counts as a correct attempt for BKT evidence.
CORRECT_THRESHOLD = 0.6

# Forgetting curve: retention = floor + (p - floor) * exp(-days / stability).
FORGET_FLOOR = 0.10
STABILITY_BASE_DAYS = 30.0  # a fully-mastered skill's ~1/e decay time
MIN_STABILITY_FRACTION = 0.15  # keep stability > 0 for near-zero mastery


@dataclass(frozen=True)
class BktParams:
    p_L0: float  # prior mastery for a never-seen KC
    p_T: float   # probability of learning per attempt (transition)
    p_S: float   # slip: knows it but answers wrong
    p_G: float   # guess: doesn't know it but answers right


_DEFAULT_PARAMS = BktParams(p_L0=0.25, p_T=0.15, p_S=0.10, p_G=0.20)

# Per-difficulty-tier overrides: harder KCs start lower and are learned slower.
_TIER_PARAMS: Dict[str, BktParams] = {
    "SL_foundation": BktParams(p_L0=0.35, p_T=0.18, p_S=0.10, p_G=0.20),
    "SL_core": BktParams(p_L0=0.25, p_T=0.15, p_S=0.10, p_G=0.20),
    "SL_advanced": BktParams(p_L0=0.18, p_T=0.12, p_S=0.12, p_G=0.18),
    "HL_core": BktParams(p_L0=0.15, p_T=0.12, p_S=0.12, p_G=0.15),
    "HL_advanced": BktParams(p_L0=0.12, p_T=0.10, p_S=0.15, p_G=0.15),
}


def bkt_update(p_L: float, correct: bool, params: BktParams) -> float:
    """Bayesian posterior mastery after one observation, with the learning step.

    Posterior given the evidence, then the transition p(L') = post + (1-post)·p_T.
    """
    if correct:
        num = p_L * (1 - params.p_S)
        denom = num + (1 - p_L) * params.p_G
    else:
        num = p_L * params.p_S
        denom = num + (1 - p_L) * (1 - params.p_G)

    posterior = num / denom if denom > 0 else p_L
    return posterior + (1 - posterior) * params.p_T


def decay_mastery(p_L: float, days_since: float, floor: float = FORGET_FLOOR) -> float:
    """Discount mastery for time elapsed since last practice.

    Stronger skills decay slower (stability scales with mastery). Never decays
    below `floor`.
    """
    if days_since <= 0:
        return p_L
    stability = STABILITY_BASE_DAYS * max(p_L, MIN_STABILITY_FRACTION)
    return floor + (p_L - floor) * math.exp(-days_since / stability)


def params_for_kc(db: Session, kc_id: int) -> BktParams:
    kc = db.query(KnowledgeComponent).filter(KnowledgeComponent.id == kc_id).first()
    if kc is None:
        return _DEFAULT_PARAMS
    return _TIER_PARAMS.get(kc.difficulty_tier, _DEFAULT_PARAMS)


def score_to_correct(grading_result: Dict) -> Optional[bool]:
    """Parse a grading result's "N/10" grade into a binary correctness signal.

    Returns None when no usable grade is present (caller should skip the update).
    """
    grade = grading_result.get("grade") if grading_result else None
    if not grade or "/" not in str(grade):
        return None
    numerator, _, denominator = str(grade).partition("/")
    try:
        got = float(numerator)
        out_of = float(denominator) or 10.0
    except ValueError:
        return None
    return (got / out_of) >= CORRECT_THRESHOLD


def _get_or_create_mastery(
    db: Session, user_id: int, kc_id: int, prior: float
) -> KCMastery:
    """Fetch the (student, KC) mastery row, locking it, or create it. Retries
    once on the create race so a concurrent insert doesn't crash the update."""
    row = (
        db.query(KCMastery)
        .filter(KCMastery.user_id == user_id, KCMastery.kc_id == kc_id)
        .with_for_update()
        .first()
    )
    if row is not None:
        return row

    row = KCMastery(user_id=user_id, kc_id=kc_id, p_mastery=prior, n_attempts=0, n_correct=0)
    db.add(row)
    try:
        db.flush()
        return row
    except IntegrityError:
        db.rollback()
        return (
            db.query(KCMastery)
            .filter(KCMastery.user_id == user_id, KCMastery.kc_id == kc_id)
            .with_for_update()
            .first()
        )


def _days_since(dt: Optional[datetime]) -> Optional[float]:
    if dt is None:
        return None
    return (datetime.utcnow() - dt).total_seconds() / 86400.0


def decayed_value(row: KCMastery) -> float:
    """Read-time mastery: the stored posterior decayed for elapsed time. Does
    not persist — persistence happens on the next `record_attempt`."""
    days = _days_since(row.last_practiced_at)
    return row.p_mastery if days is None else decay_mastery(row.p_mastery, days)


def current_mastery(db: Session, user_id: int) -> List[Dict]:
    """Per-KC decayed mastery snapshot for reads (MCP profile, retrieval)."""
    rows = (
        db.query(KCMastery, KnowledgeComponent)
        .join(KnowledgeComponent, KCMastery.kc_id == KnowledgeComponent.id)
        .filter(KCMastery.user_id == user_id)
        .all()
    )
    snapshot: List[Dict] = []
    for mastery, kc in rows:
        days = _days_since(mastery.last_practiced_at)
        snapshot.append(
            {
                "kc_id": kc.id,
                "kc_slug": kc.slug,
                "kc_name": kc.name,
                "domain": kc.domain,
                "mastery": round(decayed_value(mastery), 3),
                "raw_mastery": round(mastery.p_mastery, 3),
                "days_since_practice": round(days, 1) if days is not None else None,
                "n_attempts": mastery.n_attempts,
            }
        )
    return snapshot


def record_attempt(
    db: Session,
    user_id: int,
    question_id: int,
    practice_mode: str,
    grading_result: Dict,
) -> List[Dict]:
    """Update per-KC mastery for one graded attempt.

    Resolves the question's KCs, then for each KC decays the stored mastery for
    elapsed time and applies the BKT update. Returns a per-KC change log (also
    handy for tests). Returns [] when the question is unmapped or ungradable.
    """
    correct = score_to_correct(grading_result)
    if correct is None:
        return []

    kcs = resolve_kcs(db, question_id, practice_mode)
    if not kcs:
        return []

    now = datetime.utcnow()
    changes: List[Dict] = []

    for kc_id, _weight in kcs:
        params = params_for_kc(db, kc_id)
        row = _get_or_create_mastery(db, user_id, kc_id, params.p_L0)

        if row.last_practiced_at is not None:
            days = (now - row.last_practiced_at).total_seconds() / 86400.0
            p_before = decay_mastery(row.p_mastery, days)
        else:
            p_before = row.p_mastery

        p_after = bkt_update(p_before, correct, params)

        row.p_mastery = p_after
        row.n_attempts += 1
        row.n_correct += 1 if correct else 0
        row.last_practiced_at = now

        changes.append(
            {"kc_id": kc_id, "p_before": round(p_before, 4), "p_after": round(p_after, 4), "correct": correct}
        )

    db.commit()
    return changes
