"""Recoverable, session-bound authorization records."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from app.hashing import deterministic_id


class ApprovalStatus(StrEnum):
    ACTIVE = "active"
    CONSUMED = "consumed"
    SUPERSEDED = "superseded"


@dataclass
class ApprovalRecord:
    id: str
    offsite_id: str
    session_hash: str
    plan_hash: str
    idempotency_key_hash: str
    authorized_actions: tuple[str, ...]
    expires_at: datetime
    status: ApprovalStatus = ApprovalStatus.ACTIVE
    consumed_at: datetime | None = None

    def is_expired(self, now: datetime) -> bool:
        return now >= self.expires_at


class ApprovalStore:
    """In-memory reference semantics mirrored by the Firestore repository."""

    def __init__(self) -> None:
        self._records: dict[str, ApprovalRecord] = {}

    def authorize(
        self,
        *,
        offsite_id: str,
        session_hash: str,
        plan_hash: str,
        idempotency_key_hash: str,
        now: datetime | None = None,
    ) -> ApprovalRecord:
        timestamp = now or datetime.now(UTC)
        approval_id = deterministic_id(
            offsite_id, plan_hash, session_hash, idempotency_key_hash
        )
        if existing := self._records.get(approval_id):
            return existing

        for record in self._records.values():
            if (
                record.offsite_id == offsite_id
                and record.session_hash == session_hash
                and record.status is ApprovalStatus.ACTIVE
            ):
                record.status = ApprovalStatus.SUPERSEDED

        record = ApprovalRecord(
            id=approval_id,
            offsite_id=offsite_id,
            session_hash=session_hash,
            plan_hash=plan_hash,
            idempotency_key_hash=idempotency_key_hash,
            authorized_actions=("create_hotel", "create_room", "create_activity"),
            expires_at=timestamp + timedelta(minutes=10),
        )
        self._records[approval_id] = record
        return record

    def active_for(
        self, *, offsite_id: str, session_hash: str, plan_hash: str
    ) -> ApprovalRecord | None:
        return next(
            (
                record
                for record in self._records.values()
                if record.offsite_id == offsite_id
                and record.session_hash == session_hash
                and record.plan_hash == plan_hash
                and record.status is ApprovalStatus.ACTIVE
            ),
            None,
        )
