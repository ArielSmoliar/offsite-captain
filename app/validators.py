"""Pure deterministic validation; the model never owns these decisions."""

from datetime import timedelta

from app.models import CandidatePlan, OffsiteBrief, OriginType, ValidationFinding


def validate_plan(
    brief: OffsiteBrief, plan: CandidatePlan
) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = []
    attendees = {attendee.id: attendee for attendee in brief.attendees}
    sessions = {session.id: session for session in plan.agenda}

    for session in plan.agenda:
        for attendee_id in session.required_attendee_ids:
            attendee = attendees[attendee_id]
            buffer = timedelta(
                hours=4 if attendee.origin_type is OriginType.INTERNATIONAL else 2
            )
            if session.starts_at < attendee.arrives_at + buffer:
                findings.append(
                    ValidationFinding(
                        code="ARRIVAL_BUFFER",
                        entity_id=session.id,
                        message=f"{attendee.name} cannot reach {session.title} after the required arrival buffer.",
                    )
                )

        for dependency_id in session.depends_on:
            dependency = sessions.get(dependency_id)
            if dependency is None or dependency.ends_at > session.starts_at:
                findings.append(
                    ValidationFinding(
                        code="DEPENDENCY_ORDER",
                        entity_id=session.id,
                        message=f"{session.title} starts before dependency {dependency_id} finishes.",
                    )
                )

    for index, left in enumerate(plan.agenda):
        for right in plan.agenda[index + 1 :]:
            if left.starts_at < right.ends_at and right.starts_at < left.ends_at:
                shared = set(left.required_attendee_ids) & set(
                    right.required_attendee_ids
                )
                same_room = (
                    left.room_inventory_id
                    and left.room_inventory_id == right.room_inventory_id
                )
                if shared or same_room:
                    findings.append(
                        ValidationFinding(
                            code="DOUBLE_BOOKED",
                            entity_id=right.id,
                            message=f"{left.title} overlaps {right.title}.",
                        )
                    )

    preparation_sessions = {
        task.session_id
        for task in plan.preparation
        if task.artifact and task.owner_attendee_id
    }
    for required_id in brief.required_session_ids:
        if required_id not in preparation_sessions:
            findings.append(
                ValidationFinding(
                    code="PREP_MISSING",
                    entity_id=required_id,
                    message=f"Required session {required_id} lacks an owned preparation artifact.",
                )
            )

    if plan.total_cost_cents > brief.budget_cents:
        findings.append(
            ValidationFinding(
                code="BUDGET_EXCEEDED",
                entity_id=brief.id,
                message="Selected inventory exceeds the approved budget.",
            )
        )

    return tuple(findings)
