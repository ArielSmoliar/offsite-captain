"""Committed, reproducible hackathon scenario and acceptance oracle."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.models import (
    Attendee,
    CandidatePlan,
    InventoryKind,
    InventorySelection,
    OffsiteBrief,
    OriginType,
    PreparationTask,
    Session,
)

NY = ZoneInfo("America/New_York")


def at(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 10, day, hour, minute, tzinfo=NY)


ATTENDEES = (
    Attendee(
        id="maya",
        name="Maya",
        origin="New York",
        origin_type=OriginType.DOMESTIC,
        arrives_at=at(12, 7),
        departs_at=at(14, 19),
    ),
    Attendee(
        id="ari",
        name="Ari",
        origin="San Francisco",
        origin_type=OriginType.DOMESTIC,
        arrives_at=at(12, 7),
        departs_at=at(14, 19),
    ),
    Attendee(
        id="leo",
        name="Leo",
        origin="London",
        origin_type=OriginType.INTERNATIONAL,
        arrives_at=at(12, 10),
        departs_at=at(14, 18),
    ),
    Attendee(
        id="nina",
        name="Nina",
        origin="Berlin",
        origin_type=OriginType.INTERNATIONAL,
        arrives_at=at(12, 9, 30),
        departs_at=at(14, 18),
    ),
    Attendee(
        id="noa",
        name="Noa",
        origin="Tel Aviv",
        origin_type=OriginType.INTERNATIONAL,
        arrives_at=at(12, 8, 30),
        departs_at=at(14, 18),
        dietary=("vegetarian",),
    ),
    Attendee(
        id="sam",
        name="Sam",
        origin="New York",
        origin_type=OriginType.DOMESTIC,
        arrives_at=at(12, 7),
        departs_at=at(14, 19),
        accessibility=("step-free",),
    ),
)

BRIEF = OffsiteBrief(
    id="offsite-seed-001",
    city="New York",
    timezone="America/New_York",
    starts_at=at(12, 9),
    ends_at=at(14, 17),
    budget_cents=850_000,
    attendees=ATTENDEES,
    required_session_ids=("strategy", "fundraising", "roadmap"),
)


def inventory() -> tuple[InventorySelection, ...]:
    return (
        InventorySelection(
            inventory_id="harbor-hotel",
            kind=InventoryKind.HOTEL,
            quantity=10,
            unit_cost_cents=59_000,
            starts_at=at(12, 15),
            ends_at=at(14, 11),
            definition_version=1,
            availability_version=1,
            slot_keys=(
                "hotel:harbor-hotel:2026-10-12",
                "hotel:harbor-hotel:2026-10-13",
            ),
        ),
        InventorySelection(
            inventory_id="studio-4",
            kind=InventoryKind.ROOM,
            quantity=2,
            unit_cost_cents=45_000,
            starts_at=at(12, 14),
            ends_at=at(13, 18),
            definition_version=1,
            availability_version=1,
            slot_keys=("room:studio-4:2026-10-12", "room:studio-4:2026-10-13"),
        ),
        InventorySelection(
            inventory_id="cooking-lab",
            kind=InventoryKind.ACTIVITY,
            quantity=6,
            unit_cost_cents=19_000,
            starts_at=at(13, 16, 30),
            ends_at=at(13, 18, 30),
            definition_version=1,
            availability_version=1,
            slot_keys=("activity:cooking-lab:2026-10-13T16:30-04:00",),
        ),
    )


def invalid_plan() -> CandidatePlan:
    everyone = tuple(attendee.id for attendee in ATTENDEES)
    return CandidatePlan(
        offsite_id=BRIEF.id,
        agenda=(
            Session(
                id="strategy",
                title="Product strategy",
                starts_at=at(12, 9),
                ends_at=at(12, 11),
                required_attendee_ids=everyone,
                room_inventory_id="studio-4",
            ),
            Session(
                id="fundraising",
                title="Fundraising",
                starts_at=at(12, 16),
                ends_at=at(12, 17),
                required_attendee_ids=("maya", "ari", "leo"),
                depends_on=("strategy",),
                room_inventory_id="studio-4",
            ),
            Session(
                id="roadmap",
                title="Roadmap",
                starts_at=at(13, 9, 30),
                ends_at=at(13, 12),
                required_attendee_ids=everyone,
                depends_on=("strategy",),
                room_inventory_id="studio-4",
            ),
            Session(
                id="activity",
                title="Team cooking",
                starts_at=at(13, 11),
                ends_at=at(13, 13),
                required_attendee_ids=everyone,
            ),
        ),
        preparation=(
            PreparationTask(
                session_id="strategy",
                artifact="Strategy brief",
                owner_attendee_id="maya",
                due_at=at(9, 17),
            ),
        ),
        inventory=inventory(),
    )


def valid_plan() -> CandidatePlan:
    everyone = tuple(attendee.id for attendee in ATTENDEES)
    return CandidatePlan(
        offsite_id=BRIEF.id,
        agenda=(
            Session(
                id="strategy",
                title="Product strategy",
                starts_at=at(12, 14),
                ends_at=at(12, 16),
                required_attendee_ids=everyone,
                room_inventory_id="studio-4",
            ),
            Session(
                id="fundraising",
                title="Fundraising",
                starts_at=at(12, 16),
                ends_at=at(12, 17),
                required_attendee_ids=("maya", "ari", "leo"),
                depends_on=("strategy",),
                room_inventory_id="studio-4",
            ),
            Session(
                id="roadmap",
                title="Roadmap",
                starts_at=at(13, 9, 30),
                ends_at=at(13, 12),
                required_attendee_ids=everyone,
                depends_on=("strategy",),
                room_inventory_id="studio-4",
            ),
            Session(
                id="activity",
                title="Team cooking",
                starts_at=at(13, 16, 30),
                ends_at=at(13, 18, 30),
                required_attendee_ids=everyone,
            ),
        ),
        preparation=(
            PreparationTask(
                session_id="strategy",
                artifact="Strategy brief",
                owner_attendee_id="maya",
                due_at=at(9, 17),
            ),
            PreparationTask(
                session_id="fundraising",
                artifact="Series A decision brief",
                owner_attendee_id="ari",
                due_at=at(9, 17),
            ),
            PreparationTask(
                session_id="roadmap",
                artifact="Roadmap options",
                owner_attendee_id="nina",
                due_at=at(9, 17),
            ),
        ),
        inventory=inventory(),
    )
