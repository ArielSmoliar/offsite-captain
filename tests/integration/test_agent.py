# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import pytest
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent
from app.scenarios import BRIEF

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_ADK_TESTS") != "1",
    reason="live Vertex ADK tests require explicit quota authorization",
)


def test_agent_stream() -> None:
    """
    Integration test for the agent stream functionality.
    Tests that the agent returns valid streaming responses.
    """

    session_service = InMemorySessionService()

    session = session_service.create_session_sync(
        user_id="test_user",
        app_name="test",
        state={"offsite_id": BRIEF.id},
    )
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text="Build the authorized seeded offsite plan.")],
    )

    events = list(
        runner.run(
            new_message=message,
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    assert len(events) > 0, "Expected at least one message"

    tool_trace: list[str] = []
    for event in events:
        tool_trace.extend(call.name for call in event.get_function_calls())

    assert tool_trace[0] == "read_constraints"
    assert "validate_candidate" in tool_trace
    assert set(tool_trace).issubset(
        {
            "read_constraints",
            "search_inventory",
            "validate_candidate",
            "submit_candidate",
        }
    )
    assert tool_trace[-1] == "submit_candidate"
