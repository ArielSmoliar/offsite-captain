"""Application service joining the proposal, approval, and booking boundary."""

from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from threading import RLock
from typing import Any

from app.approvals import ApprovalRecord, ApprovalStatus, ApprovalStore
from app.booking import BookingEngine
from app.hashing import canonical_plan_hash, deterministic_id
from app.models import CandidatePlan, ConfirmationLedger, OffsiteBrief
from app.persistence import MemoryWorkflowRepository, WorkflowRepository
from app.scenarios import BRIEF, valid_plan
from app.validators import validate_plan


@dataclass(frozen=True)
class ReviewPacket:
    brief: OffsiteBrief
    plan: CandidatePlan
    plan_hash: str
    finding_count: int
    reservation_status: str


class OffsiteCoordinator:
    """Backend-owned workflow facade; the ADK agent never receives this object."""

    def __init__(
        self,
        plan: CandidatePlan | None = None,
        *,
        approvals: tuple[ApprovalRecord, ...] = (),
        ledgers: tuple[ConfirmationLedger, ...] = (),
        available_by_slot: dict[str, int] | None = None,
    ) -> None:
        plan = plan or valid_plan()
        if findings := validate_plan(BRIEF, plan):
            codes = ", ".join(sorted({finding.code for finding in findings}))
            raise ValueError(f"coordinator requires a valid plan: {codes}")
        self._plan = plan
        availability = (
            available_by_slot
            if available_by_slot is not None
            else {
                claim.slot_key: claim.quantity
                for selection in plan.inventory
                for claim in selection.claims
            }
        )
        self._approvals = ApprovalStore(approvals)
        self._booking = BookingEngine(self._approvals, availability, ledgers)

    def review(self) -> ReviewPacket:
        plan = self._plan
        findings = validate_plan(BRIEF, plan)
        reservation_status = (
            "simulated_reservations_created"
            if self._booking.has_ledger_for(plan)
            else "not_created_human_authorization_required"
        )
        return ReviewPacket(
            brief=BRIEF,
            plan=plan,
            plan_hash=canonical_plan_hash(plan),
            finding_count=len(findings),
            reservation_status=reservation_status,
        )

    def authorize(
        self, *, session_hash: str, plan_hash: str, idempotency_key: str
    ) -> ApprovalRecord:
        packet = self.review()
        if plan_hash != packet.plan_hash:
            raise ValueError("plan hash does not match the reviewable candidate")
        return self._approvals.authorize(
            offsite_id=packet.plan.offsite_id,
            session_hash=session_hash,
            plan_hash=plan_hash,
            idempotency_key_hash=deterministic_id(idempotency_key),
        )

    def reserve(
        self, *, session_hash: str, plan_hash: str, request_key: str
    ) -> ConfirmationLedger:
        packet = self.review()
        if plan_hash != packet.plan_hash:
            raise ValueError("plan hash does not match the reviewable candidate")
        return self._booking.book(
            session_hash=session_hash,
            plan=packet.plan,
            request_key=request_key,
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "plan": self._plan.model_dump(mode="json"),
            "approvals": self._approvals.snapshot(),
            "booking": self._booking.snapshot(),
        }

    @classmethod
    def from_snapshot(cls, snapshot: dict[str, Any]) -> "OffsiteCoordinator":
        approvals = tuple(
            ApprovalRecord(
                id=record["id"],
                offsite_id=record["offsite_id"],
                session_hash=record["session_hash"],
                plan_hash=record["plan_hash"],
                idempotency_key_hash=record["idempotency_key_hash"],
                authorized_actions=tuple(record["authorized_actions"]),
                expires_at=datetime.fromisoformat(record["expires_at"]),
                status=ApprovalStatus(record["status"]),
                consumed_at=(
                    datetime.fromisoformat(record["consumed_at"])
                    if record["consumed_at"]
                    else None
                ),
            )
            for record in snapshot["approvals"]
        )
        booking = snapshot["booking"]
        return cls(
            CandidatePlan.model_validate(snapshot["plan"]),
            approvals=approvals,
            ledgers=tuple(
                ConfirmationLedger.model_validate(ledger)
                for ledger in booking["ledgers"]
            ),
            available_by_slot=booking["available_by_slot"],
        )


class CoordinatorRegistry:
    """Bounded session isolation for local/demo workflow state."""

    def __init__(
        self,
        max_sessions: int = 128,
        repository: WorkflowRepository | None = None,
    ) -> None:
        if max_sessions < 1:
            raise ValueError("max_sessions must be positive")
        self._max_sessions = max_sessions
        self._repository = repository or MemoryWorkflowRepository()
        self._sessions: OrderedDict[str, OffsiteCoordinator] = OrderedDict()
        self._lock = RLock()

    def for_session(self, session_hash: str) -> OffsiteCoordinator:
        with self._lock:
            if coordinator := self._sessions.get(session_hash):
                self._sessions.move_to_end(session_hash)
                return coordinator

            snapshot = self._repository.load(session_hash)
            coordinator = (
                OffsiteCoordinator.from_snapshot(snapshot)
                if snapshot
                else OffsiteCoordinator()
            )
            self._sessions[session_hash] = coordinator
            if len(self._sessions) > self._max_sessions:
                self._sessions.popitem(last=False)
            return coordinator

    def set_plan(
        self, session_hash: str, plan: CandidatePlan
    ) -> OffsiteCoordinator:
        """Start a fresh session workflow bound to one validated exact plan."""
        coordinator = OffsiteCoordinator(plan)
        with self._lock:
            self._sessions[session_hash] = coordinator
            self._sessions.move_to_end(session_hash)
            self._repository.save(session_hash, coordinator.snapshot())
            if len(self._sessions) > self._max_sessions:
                self._sessions.popitem(last=False)
        return coordinator

    def save(self, session_hash: str) -> None:
        with self._lock:
            coordinator = self._sessions.get(session_hash)
            if coordinator is None:
                raise KeyError("session is not loaded")
            self._repository.save(session_hash, coordinator.snapshot())

    @property
    def session_count(self) -> int:
        with self._lock:
            return len(self._sessions)
