"""Programmatic ADK runner used by the operator-facing coordination endpoint."""

import logging
from dataclasses import dataclass
from uuid import uuid4

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent
from app.models import CandidatePlan
from app.scenarios import BRIEF
from app.validators import validate_plan

logger = logging.getLogger(__name__)


class LivePlanningError(RuntimeError):
    """Raised when an ADK run does not produce a valid submitted candidate."""


@dataclass(frozen=True)
class LivePlanningResult:
    plan: CandidatePlan
    tool_trace: tuple[str, ...]


async def coordinate_with_adk() -> LivePlanningResult:
    """Run one isolated Gemini/ADK planning session and return its proposal."""
    user_id = f"operator-{uuid4()}"
    session_id = f"coordination-{uuid4()}"
    sessions = InMemorySessionService()
    await sessions.create_session(
        app_name="app",
        user_id=user_id,
        session_id=session_id,
        state={"offsite_id": BRIEF.id},
    )
    runner = Runner(agent=root_agent, app_name="app", session_service=sessions)
    message = types.Content(
        role="user",
        parts=[
            types.Part.from_text(
                text=(
                    "Inspect the initial draft, repair only validator-confirmed "
                    "defects, and submit the authorized seeded offsite proposal."
                )
            )
        ],
    )
    tool_trace: list[str] = []
    event_trace: list[dict[str, object]] = []
    submitted_from_response: dict[str, object] | None = None
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=message,
    ):
        calls = [call.name for call in event.get_function_calls()]
        tool_trace.extend(calls)
        responses = event.get_function_responses()
        for response in responses:
            payload = response.response
            if (
                response.name == "submit_candidate"
                and isinstance(payload, dict)
                and payload.get("status") == "accepted"
                and isinstance(payload.get("candidate"), dict)
            ):
                submitted_from_response = payload["candidate"]
        event_trace.append(
            {
                "author": event.author,
                "calls": calls,
                "responses": [
                    response.name for response in responses
                ],
                "finish_reason": str(event.finish_reason),
                "error_code": event.error_code,
            }
        )

    session = await sessions.get_session(
        app_name="app", user_id=user_id, session_id=session_id
    )
    submitted = (
        session.state.get("submitted_candidate") if session else None
    ) or submitted_from_response
    if submitted is None:
        logger.error(
            "ADK run produced no candidate; tools=%s events=%s state_keys=%s",
            tool_trace,
            event_trace,
            sorted(session.state) if session else [],
        )
        raise LivePlanningError("ADK run completed without a submitted candidate")

    plan = CandidatePlan.model_validate(submitted)
    if findings := validate_plan(BRIEF, plan):
        codes = ", ".join(sorted({finding.code for finding in findings}))
        raise LivePlanningError(f"ADK submitted an invalid candidate: {codes}")
    return LivePlanningResult(plan=plan, tool_trace=tuple(tool_trace))
