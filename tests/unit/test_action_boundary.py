from datetime import UTC, datetime, timedelta

import pytest

from app.approvals import ApprovalStatus, ApprovalStore
from app.booking import (
    AuthorizationExpired,
    AuthorizationRequired,
    BookingEngine,
    InventoryUnavailable,
)
from app.hashing import canonical_plan_hash
from app.scenarios import valid_plan

NOW = datetime(2026, 8, 30, 14, tzinfo=UTC)
SESSION = "session-hash"


def capacities() -> dict[str, int]:
    return {
        "hotel:harbor-hotel:2026-10-12": 5,
        "hotel:harbor-hotel:2026-10-13": 5,
        "room:studio-4:2026-10-12": 1,
        "room:studio-4:2026-10-13": 1,
        "activity:cooking-lab:2026-10-13T16:30-04:00": 6,
    }


def test_booking_requires_authorization() -> None:
    engine = BookingEngine(ApprovalStore(), capacities())
    with pytest.raises(AuthorizationRequired):
        engine.book(session_hash=SESSION, plan=valid_plan(), request_key="book-1")


def test_authorization_is_recoverable_and_booking_is_idempotent() -> None:
    plan = valid_plan()
    approvals = ApprovalStore()
    first = approvals.authorize(
        offsite_id=plan.offsite_id,
        session_hash=SESSION,
        plan_hash=canonical_plan_hash(plan),
        idempotency_key_hash="approve-1",
        now=NOW,
    )
    repeated = approvals.authorize(
        offsite_id=plan.offsite_id,
        session_hash=SESSION,
        plan_hash=canonical_plan_hash(plan),
        idempotency_key_hash="approve-1",
        now=NOW + timedelta(minutes=1),
    )
    assert repeated is first

    engine = BookingEngine(approvals, capacities())
    ledger = engine.book(session_hash=SESSION, plan=plan, request_key="book-1", now=NOW)
    duplicate = engine.book(
        session_hash=SESSION, plan=plan, request_key="book-1", now=NOW
    )
    assert duplicate == ledger
    assert ledger.total_cost_cents == 794_000
    assert len(ledger.reservations) == 3
    assert first.status is ApprovalStatus.CONSUMED


def test_expiry_and_inventory_failure_are_atomic() -> None:
    plan = valid_plan()
    approvals = ApprovalStore()
    approvals.authorize(
        offsite_id=plan.offsite_id,
        session_hash=SESSION,
        plan_hash=canonical_plan_hash(plan),
        idempotency_key_hash="approve-1",
        now=NOW,
    )
    engine = BookingEngine(approvals, capacities())
    with pytest.raises(AuthorizationExpired):
        engine.book(
            session_hash=SESSION,
            plan=plan,
            request_key="expired",
            now=NOW + timedelta(minutes=10),
        )

    approvals.authorize(
        offsite_id=plan.offsite_id,
        session_hash=SESSION,
        plan_hash=canonical_plan_hash(plan),
        idempotency_key_hash="approve-2",
        now=NOW,
    )
    unavailable = capacities()
    unavailable["activity:cooking-lab:2026-10-13T16:30-04:00"] = 5
    engine = BookingEngine(approvals, unavailable)
    with pytest.raises(InventoryUnavailable):
        engine.book(session_hash=SESSION, plan=plan, request_key="unavailable", now=NOW)
