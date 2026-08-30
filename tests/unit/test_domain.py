from app.scenarios import BRIEF, invalid_plan, valid_plan
from app.state import WorkflowState, can_transition
from app.validators import validate_plan


def test_seeded_plan_exposes_exact_three_defect_classes() -> None:
    codes = {finding.code for finding in validate_plan(BRIEF, invalid_plan())}
    assert codes == {"ARRIVAL_BUFFER", "PREP_MISSING", "DOUBLE_BOOKED"}


def test_repaired_plan_is_valid_and_matches_cost_oracle() -> None:
    plan = valid_plan()
    assert validate_plan(BRIEF, plan) == ()
    assert plan.total_cost_cents == 794_000
    assert plan.total_cost_cents <= BRIEF.budget_cents
    assert len(plan.inventory) == 3


def test_action_boundary_transitions_are_explicit() -> None:
    assert can_transition(WorkflowState.AWAITING_APPROVAL, WorkflowState.APPROVED)
    assert can_transition(WorkflowState.APPROVED, WorkflowState.BOOKED)
    assert not can_transition(WorkflowState.AWAITING_APPROVAL, WorkflowState.BOOKED)
    assert not can_transition(WorkflowState.BOOKED, WorkflowState.DRAFT)
