"""Stable hashes that bind authorization to material plan fields."""

import hashlib
import json

from app.models import CandidatePlan


def canonical_plan_hash(plan: CandidatePlan) -> str:
    encoded = json.dumps(
        plan.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def deterministic_id(*parts: str, length: int = 24) -> str:
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()[:length]
