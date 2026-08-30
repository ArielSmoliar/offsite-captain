# Offsite Captain User Flow

## Flow objective

An operations lead should be able to answer four questions at every moment:

1. Where am I in the coordination process?
2. What did Offsite Captain find or change?
3. What needs my attention now?
4. Has anything actually been reserved?

The product uses one persistent workspace rather than a sequence of disconnected
dashboards or a chat transcript. The operating plan stays visible while its
state advances.

## Persistent workflow states

| State | User understanding | Primary action |
| --- | --- | --- |
| Brief | Inputs are incomplete or ready to coordinate | Coordinate offsite |
| Coordinating | The agent is inspecting constraints and inventory | Review progress |
| Needs attention | Deterministic checks found resolvable conflicts | Resolve issues |
| Ready for review | The plan is feasible and nothing is reserved | Review authorization |
| Authorized | The exact plan is approved for a limited time | Create reservations |
| Confirmed | All simulated reservations succeeded atomically | View confirmations |
| Action failed | Nothing was partially reserved | Refresh and retry safely |

The current state appears as text in the page header and as the active step in a
compact progress indicator. Color may reinforce state, but never carries it
alone.

## Screen 1: Offsite brief

### Purpose

Establish the operating constraints before the agent begins.

### Structure

- Header: `New York leadership offsite`, October 12–14, 2026.
- Readiness summary: six attendees, five origins, three required sessions,
  $8,500 budget.
- Editable sections in task order:
  1. Dates, city, and timezone.
  2. Attendees, origins, arrival/departure times.
  3. Required outcomes and sessions.
  4. Preparation requirements.
  5. Lodging, meeting-room, activity, dietary, and accessibility constraints.
- Primary action: `Coordinate offsite`.

### Clarity requirements

- Show local time and timezone beside every arrival and session time.
- Treat missing required information inline, near the affected field.
- Do not begin with an empty chat box.
- Explain the action accurately: `Build a proposal. Nothing will be reserved.`

## Screen 2: Coordination trace

### Purpose

Make agent activity understandable without exposing raw chain-of-thought.

### Structure

The workspace remains visible and a progress region reports completed operations:

1. Read six traveler constraints.
2. Compared hotel, room, and activity inventory.
3. Drafted the agenda and preparation assignments.
4. Ran deterministic feasibility checks.

Each item reports `waiting`, `in progress`, `complete`, or `needs attention`.
Technical tool payloads remain available only in a secondary details disclosure.

### Clarity requirements

- Use skeletons for pending plan sections, not a central spinner.
- Preserve completed results if a later step fails.
- Never imply that searching inventory placed a hold or created a reservation.

## Screen 3: Issues found

### Purpose

Turn validation failures into understandable, resolvable work.

### Structure

The agenda is the main surface. Three issue rows are anchored to their affected
sessions:

1. `Leo needs four hours after arrival before Product strategy.`
2. `Product strategy and Team cooking both use Studio 4 at 11:00 AM.`
3. `Fundraising and Roadmap are missing required preparation documents.`

Each issue shows the deterministic rule, affected people or resource, and the
proposed correction. One primary action, `Apply 3 fixes`, updates the plan. An
operator can expand and edit individual fixes before applying them.

### Clarity requirements

- Avoid abstract codes such as `ARRIVAL_BUFFER` in primary copy.
- State the consequence and the proposed correction together.
- After applying changes, show a concise diff: moved, reassigned, or added.

## Screen 4: Decision-ready plan

### Purpose

Let the operator verify feasibility and cost before authorization.

### Structure

- Header status: `Ready for review`.
- Validation summary: `All 11 checks passed` with a disclosure for evidence.
- Agenda: chronological, grouped by day, with required participants and room.
- Preparation: artifact, owner, due date, and related session.
- Travel-readiness view: arrival buffers and attendance coverage.
- Commitments: hotel, meeting room, and team activity.
- Cost summary: $7,940 total, $560 remaining within the $8,500 budget.
- Persistent statement: `Nothing has been reserved.`
- Primary action: `Review authorization`.
- Secondary action: `Edit plan`.

### Clarity requirements

- The total cost and unreserved status remain visible without scrolling.
- The plan, not an AI confidence percentage, is the evidence.
- Dietary and step-free requirements appear beside the relevant commitment.

## Screen 5: Authorization review

### Purpose

Make consent informed, exact, and difficult to confuse with an ordinary save.

### Structure

Use an inline authorization panel after the plan, not a modal. It summarizes:

- Exact plan version and a shortened plan identifier.
- Three simulated reservation actions.
- Total authorized amount: $7,940.
- Authorization expiry: ten minutes, with an absolute time.
- Statement: changes to the plan require new authorization.

The operator checks `I reviewed this plan and authorize these simulated
reservations`, then selects `Authorize plan`.

Authorization does not immediately reserve. The resulting state explicitly says
`Authorized until 3:42 PM` and exposes `Create 3 reservations` as the next action.

### Clarity requirements

- Never use a vague button such as `Approve`, `Continue`, or `Book now`.
- Distinguish authorization from reservation in both labels and status copy.
- Keep `Edit plan` available; editing invalidates the authorization visibly.

## Screen 6: Reservation execution

### Purpose

Show one atomic, recoverable action.

### Structure

After `Create 3 reservations`, each commitment reports progress within one
transaction region. The user cannot trigger a second request while the first is
pending. The request key remains stable across a safe retry.

Possible outcomes:

- Success: advance to Confirmed.
- Authorization expired: return to Ready for review with `Authorize again`.
- Inventory changed: show the affected commitment, confirm that nothing was
  reserved, and offer `Refresh plan`.
- Network interruption: show `Check reservation status`; do not suggest starting
  over or generating a new request.

## Screen 7: Confirmed offsite

### Purpose

Provide an operational handoff, not a celebratory dead end.

### Structure

- Status: `3 simulated reservations confirmed`.
- Confirmation ledger containing hotel, meeting room, and activity identifiers.
- Final cost: $7,940.
- Final agenda and preparation checklist.
- Audit trail: coordinated, validated, authorized, and confirmed timestamps.
- Primary action: `Open operating plan`.
- Secondary actions: `Copy confirmation summary` and `View authorization record`.

### Clarity requirements

- Say `simulated` anywhere a user might mistake the demo for a real purchase.
- Preserve the exact confirmed plan. Do not silently regenerate it.
- Present confirmations as text, not color-only success icons.

## Critical recovery paths

### User edits after authorization

Invalidate the active authorization immediately. Return the workflow to Ready
for review and state: `The plan changed. Review and authorize the new version.`

### Authorization expires

Preserve the reviewed plan and scroll position. Replace the reservation action
with `Authorize again`; do not force the operator through coordination again.

### Inventory changes before reservation

Name the affected item and show that the atomic transaction created zero
reservations. Refresh only the affected inventory, revalidate the whole plan,
and require authorization for the new plan hash.

### Repeated click or browser retry

Return the existing confirmation ledger for the same request key. The interface
states `Already completed` rather than creating or implying a duplicate.

## Demo sequence

For a concise demo, show the workflow in this order:

1. Brief ready, with global arrivals and constraints visible.
2. Coordinate, then reveal three concrete issues.
3. Apply the proposed fixes and show the plan diff.
4. Review the agenda, preparation owners, commitments, and $7,940 cost.
5. Pause on `Nothing has been reserved`.
6. Review and authorize the exact plan.
7. Create the three simulated reservations.
8. End on the confirmation ledger and finalized operating plan.

The narrative hinge is the pause between a valid proposal and human authority.
That boundary should be the clearest moment in the product.
