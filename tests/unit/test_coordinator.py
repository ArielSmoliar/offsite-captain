import pytest

from app.booking import AuthorizationRequired
from app.coordinator import CoordinatorRegistry, OffsiteCoordinator
from app.persistence import SqliteWorkflowRepository


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


def test_registry_isolates_inventory_and_approvals_by_browser_session() -> None:
    registry = CoordinatorRegistry()
    session_a = registry.for_session("browser-session-a")
    session_b = registry.for_session("browser-session-b")
    packet = session_a.review()

    session_a.authorize(
        session_hash="browser-session-a",
        plan_hash=packet.plan_hash,
        idempotency_key="approve-session-a",
    )
    session_a.reserve(
        session_hash="browser-session-a",
        plan_hash=packet.plan_hash,
        request_key="reserve-session-a",
    )

    with pytest.raises(AuthorizationRequired):
        session_b.reserve(
            session_hash="browser-session-b",
            plan_hash=packet.plan_hash,
            request_key="reserve-session-b",
        )

    session_b.authorize(
        session_hash="browser-session-b",
        plan_hash=packet.plan_hash,
        idempotency_key="approve-session-b",
    )
    ledger_b = session_b.reserve(
        session_hash="browser-session-b",
        plan_hash=packet.plan_hash,
        request_key="reserve-session-b",
    )
    assert len(ledger_b.reservations) == 3


def test_registry_evicts_oldest_session_at_capacity() -> None:
    registry = CoordinatorRegistry(max_sessions=2)
    first = registry.for_session("browser-session-a")
    registry.for_session("browser-session-b")
    registry.for_session("browser-session-c")

    assert registry.session_count == 2
    assert registry.for_session("browser-session-a") is not first


def test_sqlite_repository_restores_authorization_and_idempotent_ledger(
    tmp_path,
) -> None:
    repository = SqliteWorkflowRepository(tmp_path / "workflow.db")
    session_hash = "durable-browser-session"
    request_key = "durable-reservation-request"

    first_registry = CoordinatorRegistry(repository=repository)
    first = first_registry.set_plan(session_hash, OffsiteCoordinator().review().plan)
    packet = first.review()
    first.authorize(
        session_hash=session_hash,
        plan_hash=packet.plan_hash,
        idempotency_key="durable-approval-key",
    )
    first_registry.save(session_hash)

    restarted_registry = CoordinatorRegistry(repository=repository)
    restarted = restarted_registry.for_session(session_hash)
    ledger = restarted.reserve(
        session_hash=session_hash,
        plan_hash=packet.plan_hash,
        request_key=request_key,
    )
    restarted_registry.save(session_hash)

    second_restart = CoordinatorRegistry(repository=repository)
    repeated = second_restart.for_session(session_hash).reserve(
        session_hash=session_hash,
        plan_hash=packet.plan_hash,
        request_key=request_key,
    )

    assert repeated == ledger
    assert len(repeated.reservations) == 3
