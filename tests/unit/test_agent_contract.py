from app.agent import MODEL_ID, root_agent


def test_agent_uses_required_model_and_bounded_tools() -> None:
    assert MODEL_ID == "gemini-3.5-flash"
    assert root_agent.name == "offsite_captain"
    assert {tool.__name__ for tool in root_agent.tools} == {
        "read_constraints",
        "search_inventory",
        "validate_candidate",
        "submit_candidate",
    }


def test_agent_instruction_preserves_action_boundary() -> None:
    instruction = str(root_agent.instruction)
    assert "Never claim that a reservation exists" in instruction
    assert "human authorization" in instruction
