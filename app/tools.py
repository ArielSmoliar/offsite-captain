"""Bounded, read/propose-only ADK tools for the planning agent."""

import hashlib
import json
from typing import Any

from google.adk.tools import ToolContext
from pydantic import ValidationError

from app.models import CandidatePlan, InventoryKind
from app.scenarios import BRIEF, invalid_plan, inventory
from app.validators import validate_plan


def _require_authorized_context(tool_context: ToolContext) -> None:
    offsite_id = tool_context.state.get("offsite_id")
    if offsite_id != BRIEF.id:
        raise ValueError("authorized offsite context is missing or invalid")


def _candidate_fingerprint(candidate: dict[str, Any]) -> str:
    encoded = json.dumps(
        candidate, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def read_constraints(tool_context: ToolContext) -> dict[str, Any]:
    """Read the authorized offsite brief and deterministic scheduling rules."""
    _require_authorized_context(tool_context)
    return {
        "status": "success",
        "brief": BRIEF.model_dump(mode="json"),
        "initial_draft": invalid_plan().model_dump(mode="json"),
        "rules": {
            "domestic_arrival_buffer_hours": 2,
            "international_arrival_buffer_hours": 4,
            "budget_cents": BRIEF.budget_cents,
            "required_preparation_for": list(BRIEF.required_session_ids),
        },
    }


def search_inventory(
    kind: str, filters: dict[str, str], tool_context: ToolContext
) -> dict[str, Any]:
    """Return compatible synthetic inventory for one provider category."""
    _require_authorized_context(tool_context)
    try:
        requested_kind = InventoryKind(kind)
    except ValueError:
        return {"status": "error", "code": "UNKNOWN_INVENTORY_KIND", "results": []}

    if filters.get("city", BRIEF.city).casefold() != BRIEF.city.casefold():
        return {"status": "success", "results": []}

    results = [
        item.model_dump(mode="json")
        for item in inventory()
        if item.kind is requested_kind
    ]
    return {"status": "success", "results": results}


def validate_candidate(
    candidate: dict[str, Any], tool_context: ToolContext
) -> dict[str, Any]:
    """Validate a candidate using backend-owned deterministic rules."""
    _require_authorized_context(tool_context)
    fingerprint = _candidate_fingerprint(candidate)
    cache = dict(tool_context.state.get("validation_cache", {}))
    if cached := cache.get(fingerprint):
        return cached
    # One seeded draft plus at most two model-produced candidates.
    if len(cache) >= 3:
        return {
            "status": "rejected",
            "code": "VALIDATION_ATTEMPT_LIMIT",
            "findings": [],
        }

    try:
        plan = CandidatePlan.model_validate(candidate)
    except ValidationError as exc:
        response = {
            "status": "invalid",
            "code": "SCHEMA_INVALID",
            "errors": exc.errors(include_input=False, include_url=False),
        }
        cache[fingerprint] = response
        tool_context.state["validation_cache"] = cache
        return response

    findings = validate_plan(BRIEF, plan)
    response = {
        "status": "valid" if not findings else "invalid",
        "total_cost_cents": plan.total_cost_cents,
        "findings": [finding.model_dump(mode="json") for finding in findings],
    }
    cache[fingerprint] = response
    tool_context.state["validation_cache"] = cache
    return response


def submit_candidate(
    candidate: dict[str, Any], tool_context: ToolContext
) -> dict[str, Any]:
    """Submit a validated candidate; this tool never creates reservations."""
    validation = validate_candidate(candidate, tool_context)
    if validation["status"] != "valid":
        return {"status": "rejected", "validation": validation}

    plan = CandidatePlan.model_validate(candidate)
    tool_context.state["submitted_candidate"] = plan.model_dump(mode="json")
    return {
        "status": "accepted",
        "total_cost_cents": plan.total_cost_cents,
        "reservation_status": "not_created_human_authorization_required",
    }
