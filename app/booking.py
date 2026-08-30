"""Atomic reference implementation for idempotent simulated booking."""

from datetime import UTC, datetime
from threading import RLock

from app.approvals import ApprovalStatus, ApprovalStore
from app.hashing import canonical_plan_hash, deterministic_id
from app.models import CandidatePlan, ConfirmationLedger, Reservation


class BookingError(RuntimeError):
    code = "BOOKING_ERROR"


class AuthorizationRequired(BookingError):
    code = "AUTHORIZATION_REQUIRED"


class AuthorizationExpired(BookingError):
    code = "AUTHORIZATION_EXPIRED"


class InventoryUnavailable(BookingError):
    code = "INVENTORY_UNAVAILABLE"


class BookingEngine:
    def __init__(
        self, approvals: ApprovalStore, available_by_slot: dict[str, int]
    ) -> None:
        self._approvals = approvals
        self._available_by_slot = available_by_slot.copy()
        self._ledgers: dict[str, ConfirmationLedger] = {}
        self._lock = RLock()

    def book(
        self,
        *,
        session_hash: str,
        plan: CandidatePlan,
        request_key: str,
        now: datetime | None = None,
    ) -> ConfirmationLedger:
        timestamp = now or datetime.now(UTC)
        plan_hash = canonical_plan_hash(plan)
        ledger_id = deterministic_id(plan.offsite_id, plan_hash, request_key)

        with self._lock:
            if existing := self._ledgers.get(ledger_id):
                return existing

            approval = self._approvals.active_for(
                offsite_id=plan.offsite_id,
                session_hash=session_hash,
                plan_hash=plan_hash,
            )
            if approval is None:
                raise AuthorizationRequired("active authorization not found")
            if approval.is_expired(timestamp):
                raise AuthorizationExpired("authorization has expired")

            for selection in plan.inventory:
                for claim in selection.claims:
                    if self._available_by_slot.get(claim.slot_key, 0) < claim.quantity:
                        raise InventoryUnavailable(claim.slot_key)

            for selection in plan.inventory:
                for claim in selection.claims:
                    self._available_by_slot[claim.slot_key] -= claim.quantity

            reservations = tuple(
                Reservation(
                    id=deterministic_id(
                        plan.offsite_id,
                        plan_hash,
                        request_key,
                        selection.inventory_id,
                    ),
                    offsite_id=plan.offsite_id,
                    plan_hash=plan_hash,
                    request_key=request_key,
                    inventory_id=selection.inventory_id,
                    quantity=selection.quantity,
                    cost_cents=selection.subtotal_cents,
                    confirmation_id=f"OC-{deterministic_id(selection.inventory_id, ledger_id, length=10).upper()}",
                )
                for selection in plan.inventory
            )
            ledger = ConfirmationLedger(
                offsite_id=plan.offsite_id,
                plan_hash=plan_hash,
                request_key=request_key,
                total_cost_cents=plan.total_cost_cents,
                reservations=reservations,
            )
            self._ledgers[ledger_id] = ledger
            approval.status = ApprovalStatus.CONSUMED
            approval.consumed_at = timestamp
            return ledger
