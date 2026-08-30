"""HTTP boundary for the operator-facing Offsite Captain workflow."""

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from app.booking import BookingError
from app.coordinator import OffsiteCoordinator
from app.hashing import canonical_plan_hash
from app.live_planner import coordinate_with_adk
from app.scenarios import BRIEF, invalid_plan
from app.validators import validate_plan

router = APIRouter(prefix="/product/api", tags=["product"])
coordinator = OffsiteCoordinator()


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AuthorizationRequest(StrictRequest):
    session_hash: str
    plan_hash: str
    idempotency_key: str


class ReservationRequest(StrictRequest):
    session_hash: str
    plan_hash: str
    request_key: str


@router.get("/review")
def get_review() -> dict[str, Any]:
    packet = coordinator.review()
    return {
        "brief": packet.brief.model_dump(mode="json"),
        "plan": packet.plan.model_dump(mode="json"),
        "plan_hash": packet.plan_hash,
        "finding_count": packet.finding_count,
        "reservation_status": packet.reservation_status,
    }


@router.post("/coordinate")
async def coordinate(
    mode: Literal["deterministic", "live"] = "deterministic",
) -> dict[str, Any]:
    """Run the committed defective draft through deterministic validation."""
    draft = invalid_plan()
    findings = validate_plan(BRIEF, draft)
    response: dict[str, Any] = {
        "brief": BRIEF.model_dump(mode="json"),
        "draft": draft.model_dump(mode="json"),
        "findings": [finding.model_dump(mode="json") for finding in findings],
        "reservation_status": "not_created",
        "agent_mode": "deterministic",
    }
    if mode == "live":
        try:
            live = await coordinate_with_adk()
            response.update(
                agent_mode="gemini_adk",
                repaired_plan=live.plan.model_dump(mode="json"),
                plan_hash=canonical_plan_hash(live.plan),
                tool_trace=live.tool_trace,
            )
        except Exception as exc:
            response.update(
                agent_mode="deterministic_fallback",
                fallback_reason=type(exc).__name__,
            )
    return response


@router.post("/authorize")
def authorize(request: AuthorizationRequest) -> dict[str, Any]:
    try:
        approval = coordinator.authorize(
            session_hash=request.session_hash,
            plan_hash=request.plan_hash,
            idempotency_key=request.idempotency_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "id": approval.id,
        "status": approval.status,
        "plan_hash": approval.plan_hash,
        "authorized_actions": approval.authorized_actions,
        "expires_at": approval.expires_at.isoformat(),
    }


@router.post("/reserve")
def reserve(request: ReservationRequest) -> dict[str, Any]:
    try:
        ledger = coordinator.reserve(
            session_hash=request.session_hash,
            plan_hash=request.plan_hash,
            request_key=request.request_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except BookingError as exc:
        raise HTTPException(
            status_code=409, detail={"code": exc.code, "message": str(exc)}
        ) from exc
    return ledger.model_dump(mode="json")
