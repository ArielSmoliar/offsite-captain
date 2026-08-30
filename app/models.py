"""Domain models for the deterministic Offsite Captain core."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class OriginType(StrEnum):
    DOMESTIC = "domestic"
    INTERNATIONAL = "international"


class InventoryKind(StrEnum):
    HOTEL = "hotel"
    ROOM = "room"
    ACTIVITY = "activity"


class Attendee(StrictModel):
    id: str
    name: str
    origin: str
    origin_type: OriginType
    arrives_at: datetime
    departs_at: datetime
    dietary: tuple[str, ...] = ()
    accessibility: tuple[str, ...] = ()


class Session(StrictModel):
    id: str
    title: str
    starts_at: datetime
    ends_at: datetime
    required_attendee_ids: tuple[str, ...]
    depends_on: tuple[str, ...] = ()
    room_inventory_id: str | None = None

    @model_validator(mode="after")
    def ends_after_start(self) -> Session:
        if self.ends_at <= self.starts_at:
            raise ValueError("session end must be after start")
        return self


class PreparationTask(StrictModel):
    session_id: str
    artifact: str
    owner_attendee_id: str
    due_at: datetime


class InventorySelection(StrictModel):
    inventory_id: str
    kind: InventoryKind
    quantity: int = Field(gt=0)
    unit_cost_cents: int = Field(ge=0)
    starts_at: datetime
    ends_at: datetime
    definition_version: int = Field(gt=0)
    availability_version: int = Field(gt=0)
    slot_keys: tuple[str, ...]

    @property
    def subtotal_cents(self) -> int:
        return self.quantity * self.unit_cost_cents


class OffsiteBrief(StrictModel):
    id: str
    city: str
    timezone: str
    starts_at: datetime
    ends_at: datetime
    budget_cents: int = Field(gt=0)
    attendees: tuple[Attendee, ...]
    required_session_ids: tuple[str, ...]


class CandidatePlan(StrictModel):
    offsite_id: str
    agenda: tuple[Session, ...]
    preparation: tuple[PreparationTask, ...]
    inventory: tuple[InventorySelection, ...]

    @property
    def total_cost_cents(self) -> int:
        return sum(item.subtotal_cents for item in self.inventory)


class ValidationFinding(StrictModel):
    code: str
    message: str
    entity_id: str
