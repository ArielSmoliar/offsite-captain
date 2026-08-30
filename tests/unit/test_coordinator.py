import pytest

from app.booking import AuthorizationRequired
from app.coordinator import OffsiteCoordinator


def test_review_packet_is_valid_and_requires_human_authorization() -> None:
    coordinator = OffsiteCoordinator()

    packet = coordinator.review()

    assert packet.finding_count == 0
    assert packet.plan.total_cost_cents == 794_000
    assert packet.reservation_status.endswith("human_authorization_required")


def test_review_cannot_be_reserved_before_exact_plan_is_authorized() -> None:
    coordinator = OffsiteCoordinator()
    packet = coordinator.review()

    with pytest.raises(AuthorizationRequired):
        coordinator.reserve(
            session_hash="browser-session-a",
            plan_hash=packet.plan_hash,
            request_key="reserve-1",
        )


def test_authorized_review_returns_idempotent_confirmation_ledger() -> None:
    coordinator = OffsiteCoordinator()
    packet = coordinator.review()
    coordinator.authorize(
        session_hash="browser-session-a",
        plan_hash=packet.plan_hash,
        idempotency_key="approve-1",
    )

    first = coordinator.reserve(
        session_hash="browser-session-a",
        plan_hash=packet.plan_hash,
        request_key="reserve-1",
    )
    repeated = coordinator.reserve(
        session_hash="browser-session-a",
        plan_hash=packet.plan_hash,
        request_key="reserve-1",
    )

    assert repeated == first
    assert len(first.reservations) == 3


def test_authorization_rejects_a_stale_or_tampered_plan_hash() -> None:
    coordinator = OffsiteCoordinator()

    with pytest.raises(ValueError, match="plan hash"):
        coordinator.authorize(
            session_hash="browser-session-a",
            plan_hash="stale-plan",
            idempotency_key="approve-1",
        )
