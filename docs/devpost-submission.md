# Devpost submission draft

This file is preparation material. Do not submit it without the entrant’s final
explicit approval.

## Project identity

- **Title:** Offsite Captain
- **Tagline:** Turn a messy startup offsite into one feasible, authorized run sheet.
- **Category:** Taskmaster
- **Submitter type:** Individuals
- **Project start date:** 08-30-26
- **Repository:** https://github.com/ArielSmoliar/offsite-captain
- **Hosted project:** https://offsite-captain-pgg2be7x2a-ue.a.run.app/product/
- **Built with:** Gemini 3.5 Flash, Vertex AI, Google ADK, Cloud Run, Firestore,
  FastAPI, Pydantic, Python, JavaScript
- **Video URL:** https://youtu.be/TrWWCVCx-yI
- **Architecture upload:** `diagrams/offsite-captain-architecture.png`

## Short description

Offsite Captain coordinates a distributed startup offsite from constraints to a
decision-ready plan, then pauses at an exact human authorization boundary before
creating atomic, idempotent simulated reservations.

## Full write-up

### Inspiration

Startup offsites look simple until one person has to reconcile international
arrival buffers, a fixed budget, meeting dependencies, preparation ownership,
dietary and accessibility needs, hotel inventory, rooms, and activities. The
work usually lives across messages and spreadsheets, and the failure is often
discovered after a reservation or calendar commitment has already been made.

Offsite Captain treats the plan as an operating object. It coordinates the
details autonomously, makes conflicts visible, and keeps consequential action
behind a precise human approval.

### What it does

The demo starts with a seeded offsite draft containing real operational defects:
international attendees cannot reach early sessions after the required arrival
buffer, one attendee is double-booked, and two required sessions lack owned
preparation artifacts.

Gemini 3.5 Flash on Vertex AI uses bounded Google ADK tools to read the brief,
search synthetic hotel, meeting-room, and activity inventory, validate the
candidate, repair cited defects, and submit a proposal. Deterministic validators
remain authoritative for schedule feasibility, dependencies, attendance,
preparation ownership, budget, inventory quantities, and inventory versions.

The operator then reviews one run sheet with the agenda, assignments,
assumptions, exceptions, total cost, and canonical plan hash. Nothing is reserved
until a human authorizes that exact hash. The backend binds authorization to the
session, scope, cost, and expiry, then creates three simulated reservation
requests atomically. Repeating the same request key returns the original
confirmation ledger.

### How we built it

- **Gemini 3.5 Flash on Vertex AI** performs constrained planning and repair.
- **Google ADK** exposes only bounded read, search, validate, and propose tools.
- **FastAPI on Cloud Run** serves the operator interface and action boundary.
- **Firestore** persists reviewed plans, approvals, inventory consumption, and
  ledgers across process and revision restarts.
- **Pydantic models and deterministic validators** own business invariants.
- **Canonical hashing, expiring approvals, and idempotency keys** prevent stale,
  cross-session, partial, and duplicate action.
- **Memory and SQLite adapters** support tests and restart-safe local development.

The Cloud Run service uses a dedicated runtime identity with no stored service
account key. Until Firestore compare-and-swap transactions are implemented, the
service is capped at one instance with concurrency eight to preserve serialized
booking semantics.

### Data sources

All attendee constraints, hotel inventory, rooms, activities, prices, and
reservations are synthetic and committed in the repository. The application
does not purchase travel, contact providers, or use private customer data.

### Challenges

The hard problem was separating plausible language-model output from authorized
action. A useful plan is not necessarily feasible, a feasible plan is not
approved, and an approved plan can still become stale. We kept those as separate
states and made deterministic code, rather than the model, responsible for the
transitions that protect users.

Persistence required the same discipline. Atomic and idempotent behavior worked
in memory first, then had to survive process restarts and shared hosting. The
repository boundary supports memory, SQLite, and Firestore without giving the
model direct database or booking access.

### Accomplishments

- A plan-first operator interface rather than a chat wrapper.
- Live Gemini/ADK repair of arrival, scheduling, and preparation defects.
- Exact-plan, session-bound, expiring human authorization.
- Atomic creation of hotel, room, and activity simulation records.
- Idempotent replay with an identical confirmation ledger.
- Safe recovery for stale plans, expired approvals, inventory changes, and
  interrupted requests.
- A 28-test deterministic baseline and ADK evaluation scoring 100% on response
  quality, hallucination, action-boundary, and tool-policy metrics.
- A dedicated Cloud Run and Firestore deployment verified through the full
  anonymous hosted workflow.

### What we learned

Agent autonomy becomes more useful when its authority is narrower and clearer.
Gemini is good at repairing a constrained proposal, while deterministic code is
better at enforcing budgets, versions, dependencies, and authorization. The
strong design is not “model versus rules”; it is a state machine in which each
owns the work it can prove.

We also learned that idempotency must be designed with authorization and
persistence, not added after booking logic. Binding approval to a canonical hash
and returning the original ledger on replay makes interruptions recoverable
without asking the operator to guess what happened.

### What’s next

The next production step is Firestore compare-and-swap transactions so the
service can safely scale beyond one instance. After that: real operator-supplied
briefs, auditable plan edits that invalidate prior authorization, role-based
approval, and optional provider adapters that remain disabled until explicitly
configured.

## Required custom answers

- **Submitter Type:** Individuals
- **Submitter country of residence:** United States
- **Category:** Taskmaster
- **Organization name:** Not applicable; use `N/A` if the required field does
  not accept an empty answer
- **Project start date:** 08-30-26
- **Code repository:** https://github.com/ArielSmoliar/offsite-captain
- **Reproducible testing instructions in README:** Yes
- **Hosted project URL:** https://offsite-captain-pgg2be7x2a-ue.a.run.app/product/
- **Google SDK:** Agent Development Kit (ADK)
- **Google Cloud services:** Cloud Run, Firestore
- **Google AI model:** Gemini 3.5 Flash on Vertex AI
- **Startup prize:** Do not opt in unless the entrant separately supplies an
  incorporated organization name and corporate email address
- **Bonus content/social links:** Leave blank unless supplied by the entrant

## Judge testing instructions

1. Open the hosted URL in a private browser window; no account or credentials
   are required.
2. Click **Coordinate offsite** and wait for the Gemini/ADK trace to finish.
3. Review the six seeded findings and repaired plan. Confirm the page still says
   no reservation exists.
4. Authorize the exact plan in the authorization panel.
5. Create the simulated reservations and inspect the three confirmation IDs.
6. Retry the request if offered; the ledger must remain identical.

All inventory and reservations are simulated. The demo and testing flow must
show a completed Gemini 3.5 Flash proposal through Google ADK before review,
authorization, or simulated reservation creation.

## Final submission gates

- Confirm the organization field accepts `N/A`.
- Upload `diagrams/offsite-captain-architecture.png` to the architecture field.
- Confirm the public hosted URL, repository, and video all load anonymously.
- Do not add a repository license without the entrant's separate explicit
  approval.
- Review the complete form, then obtain separate explicit approval before the
  Devpost submission action.
