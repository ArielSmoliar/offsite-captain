"""Application service joining the proposal, approval, and booking boundary."""

from dataclasses import dataclass

from app.approvals import ApprovalRecord, ApprovalStore
from app.booking import BookingEngine
from app.hashing import canonical_plan_hash, deterministic_id
from app.models import CandidatePlan, ConfirmationLedger, OffsiteBrief
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

    def __init__(self) -> None:
        plan = valid_plan()
        available_by_slot = {
            claim.slot_key: claim.quantity
            for selection in plan.inventory
            for claim in selection.claims
        }
        self._approvals = ApprovalStore()
        self._booking = BookingEngine(self._approvals, available_by_slot)

    def review(self) -> ReviewPacket:
        plan = valid_plan()
        findings = validate_plan(BRIEF, plan)
        return ReviewPacket(
            brief=BRIEF,
            plan=plan,
            plan_hash=canonical_plan_hash(plan),
            finding_count=len(findings),
            reservation_status="not_created_human_authorization_required",
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
