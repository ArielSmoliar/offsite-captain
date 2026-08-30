"""Programmatic ADK runner used by the operator-facing coordination endpoint."""

from dataclasses import dataclass
from uuid import uuid4

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent
from app.models import CandidatePlan
from app.scenarios import BRIEF
from app.validators import validate_plan


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
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=message,
    ):
        tool_trace.extend(call.name for call in event.get_function_calls())

    session = await sessions.get_session(
        app_name="app", user_id=user_id, session_id=session_id
    )
    submitted = session.state.get("submitted_candidate") if session else None
    if submitted is None:
        raise LivePlanningError("ADK run completed without a submitted candidate")

    plan = CandidatePlan.model_validate(submitted)
    if findings := validate_plan(BRIEF, plan):
        codes = ", ".join(sorted({finding.code for finding in findings}))
        raise LivePlanningError(f"ADK submitted an invalid candidate: {codes}")
    return LivePlanningResult(plan=plan, tool_trace=tuple(tool_trace))
