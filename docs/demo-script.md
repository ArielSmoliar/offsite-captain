# Offsite Captain demo script

Target length: 3:25. Hard limit: 4:00. Record in English at 1440p or 1080p with
the browser zoomed so plan state, action labels, and confirmation IDs are legible.

## Before recording

- Open the hosted product at
  `https://offsite-captain-pgg2be7x2a-ue.a.run.app/product/` in a fresh private
  window and confirm it loads without credentials.
- Open Google Cloud Console to project `offsite-captain-2026`, Cloud Run service
  `offsite-captain`, with the service URL and latest ready revision visible.
- Keep the GitHub README architecture diagram open in a third tab.
- Start from a fresh browser session so the demo has no prior authorization or
  reservation state.
- Hide bookmarks, notifications, account details, billing details, tokens, and
  any terminal containing credentials.
- Record one clean live take. If editing is necessary, do not splice separate
  product outcomes into a misleading sequence.

## Timed narration and actions

### 0:00–0:15 — Show the product working first

Action: Start on the hosted run sheet. Click **Coordinate offsite** immediately.

Narration: “Offsite Captain turns a distributed startup’s travel constraints,
meeting dependencies, preparation work, venue inventory, and budget into one
feasible operating plan. This is the live Cloud Run application.”

### 0:15–0:50 — Prove autonomous coordination

Action: Let the coordination trace complete. Point to the seeded arrival-buffer,
double-booking, and missing-preparation findings, then the repaired plan.

Narration: “Gemini 3.5 Flash on Vertex AI uses bounded Google ADK tools to read
the brief, search synthetic inventory, validate a candidate, repair the defects,
and submit a proposal. The model cannot authorize or reserve anything.
Deterministic validators own feasibility, dependencies, inventory versions, and
budget.”

### 0:50–1:25 — Show the decision-ready plan

Action: Scroll through the agenda, assignments, inventory, assumptions, cost,
and canonical plan hash.

Narration: “The operator reviews the plan itself, not a chat transcript. Every
required session has feasible attendance and owned preparation. The total is
$7,940 against an $8,500 budget. Nothing has been reserved.”

### 1:25–2:05 — Prove the human action boundary

Action: Open the authorization panel, acknowledge the exact scope, and click the
authorization control. Pause on the active authorization record.

Narration: “A human must authorize the exact canonical plan hash. The approval
is session-bound, cost-bound, action-scoped, and expires after ten minutes. Any
plan change, inventory change, expired approval, or different browser session
fails safely.”

### 2:05–2:40 — Prove atomic, idempotent action

Action: Create the simulated reservations. Show all three confirmations and the
preserved authorization record. Use the retry control if visible.

Narration: “The backend now creates hotel, room, and activity reservation
requests as one atomic operation. All inventory is simulated. Retrying the same
request returns the same ledger, so a network interruption cannot create
duplicates or a partial booking.”

### 2:40–3:05 — Prove Google Cloud

Action: Switch to Cloud Run Console. Show project `offsite-captain-2026`, service
`offsite-captain`, region `us-east1`, the `.run.app` URL, one-instance cap, and
latest ready revision. Do not expose billing or identity details.

Narration: “The backend runs on Google Cloud Run with Firestore workflow state
and Vertex AI. Until Firestore compare-and-swap transactions ship, Cloud Run is
capped at one instance with concurrency eight to preserve serialized booking
semantics.”

### 3:05–3:25 — Close on architecture and value

Action: Switch to the README architecture diagram.

Narration: “Offsite Captain removes the messy coordination work while keeping
high-impact action under exact human control. Gemini proposes, deterministic
systems validate, humans authorize, and the backend acts safely.”

## Upload checklist

- Final runtime is below 4:00, ideally 3:20–3:35.
- Product action begins within the first 15 seconds.
- Cloud Run proof and the public `.run.app` URL are readable.
- The video is public, not unlisted, on YouTube or Vimeo.
- Incognito playback works at 1080p and captions are accurate.
- Description links to the hosted product and public GitHub repository.
- No credentials, private values, email addresses, billing data, or tokens are
  visible in any frame.
