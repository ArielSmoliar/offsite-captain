"""Explicit workflow states and transitions."""

from enum import StrEnum


class WorkflowState(StrEnum):
    DRAFT = "draft"
    ENQUEUE_PENDING = "enqueue_pending"
    QUEUED = "queued"
    PLANNING = "planning"
    VALIDATING = "validating"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    BOOKED = "booked"
    FAILED_PLANNING = "failed_planning"
    FAILED_VALIDATION = "failed_validation"


ALLOWED_TRANSITIONS: dict[WorkflowState, frozenset[WorkflowState]] = {
    WorkflowState.DRAFT: frozenset({WorkflowState.ENQUEUE_PENDING}),
    WorkflowState.ENQUEUE_PENDING: frozenset({WorkflowState.QUEUED}),
    WorkflowState.QUEUED: frozenset(
        {WorkflowState.PLANNING, WorkflowState.FAILED_PLANNING}
    ),
    WorkflowState.PLANNING: frozenset(
        {WorkflowState.VALIDATING, WorkflowState.FAILED_PLANNING}
    ),
    WorkflowState.VALIDATING: frozenset(
        {WorkflowState.AWAITING_APPROVAL, WorkflowState.FAILED_VALIDATION}
    ),
    WorkflowState.AWAITING_APPROVAL: frozenset({WorkflowState.APPROVED}),
    WorkflowState.APPROVED: frozenset(
        {WorkflowState.AWAITING_APPROVAL, WorkflowState.BOOKED}
    ),
    WorkflowState.BOOKED: frozenset(),
    WorkflowState.FAILED_PLANNING: frozenset(),
    WorkflowState.FAILED_VALIDATION: frozenset(),
}


def can_transition(current: WorkflowState, target: WorkflowState) -> bool:
    return target in ALLOWED_TRANSITIONS[current]
