from typing import Any, cast

from google.adk.tools import ToolContext

from app.scenarios import invalid_plan, valid_plan
from app.tools import submit_candidate, validate_candidate


class FakeToolContext:
    def __init__(self) -> None:
        self.state: dict[str, Any] = {"offsite_id": "offsite-seed-001"}


def context() -> ToolContext:
    return cast(ToolContext, FakeToolContext())


def test_validation_reuses_identical_candidate_result() -> None:
    tool_context = context()
    candidate = invalid_plan().model_dump(mode="json")

    first = validate_candidate(candidate, tool_context)
    repeated = validate_candidate(candidate, tool_context)

    assert repeated == first
    assert len(tool_context.state["validation_cache"]) == 1


def test_validation_allows_seed_plus_two_distinct_model_attempts() -> None:
    tool_context = context()
    validate_candidate(invalid_plan().model_dump(mode="json"), tool_context)
    validate_candidate(valid_plan().model_dump(mode="json"), tool_context)
    second_model_attempt = valid_plan().model_copy(
        update={"preparation": valid_plan().preparation[:-1]}
    )
    validate_candidate(second_model_attempt.model_dump(mode="json"), tool_context)
    over_limit = valid_plan().model_copy(
        update={"preparation": valid_plan().preparation[:-2]}
    )

    response = validate_candidate(over_limit.model_dump(mode="json"), tool_context)

    assert response["status"] == "rejected"
    assert response["code"] == "VALIDATION_ATTEMPT_LIMIT"


def test_submit_candidate_returns_the_accepted_validated_payload() -> None:
    tool_context = context()
    candidate = valid_plan().model_dump(mode="json")

    response = submit_candidate(candidate, tool_context)

    assert response["status"] == "accepted"
    assert response["candidate"] == candidate
    assert tool_context.state["submitted_candidate"] == candidate
