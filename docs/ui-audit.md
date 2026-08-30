# Offsite Captain UI Audit

Date: August 30, 2026  
Surface: `frontend/index.html`, `frontend/app.js`, `frontend/styles.css`  
Method: Impeccable product-register audit plus direct semantic, token,
interaction, responsive, and contrast inspection.

## Remediation update

The P1 hardening pass is complete. Coordination now has an in-context retry,
progress exposes textual states with `aria-busy`, focus moves to the revealed
issues heading, and the shared status band distinguishes success, information,
and recoverable warning states. Copy feedback also uses a dedicated live region.

Revised score: **18/20 (Excellent, minor polish)**. Remaining findings are the
P2 edit-plan decision, touch-target sizing, and truthful progressive timing,
plus the P3 product-heading and design-system documentation work.

The Impeccable CLI package installation stalled and was terminated without
changing the repository. The findings below are based on verified source and
computed contrast values.

## Audit health score

| # | Dimension | Score | Key finding |
| --- | --- | --- | --- |
| 1 | Accessibility | 2/4 | Dynamic progress and focus changes are not fully announced |
| 2 | Performance | 4/4 | Small dependency-free frontend with bounded motion |
| 3 | Responsive design | 3/4 | Structural breakpoints are good; some text controls miss 44 px targets |
| 4 | Theming | 3/4 | Strong OKLCH tokens; missing warning and error state tokens |
| 5 | Anti-patterns | 4/4 | No material AI-interface tells |
| **Total** |  | **16/20** | **Good** |

## Anti-pattern verdict

**Pass.** The interface does not look like a generic AI dashboard. The plan is
the primary object, the palette is restrained, familiar controls are used, and
there is no gradient text, glass effect, decorative animation, card-grid filler,
or chat-first framing. The disabled `Edit plan` action is the one conspicuous
prototype artifact.

## Executive summary

- Audit health score: **16/20 (Good)**
- Issues: **0 P0, 4 P1, 4 P2, 1 P3**
- Measured text contrast is strong: muted text on paper is 5.93:1, accent on
  paper is 6.76:1, success text on its tint is 6.21:1, and primary-button text
  is 7.05:1.
- The highest-risk gap is recovery from a failed coordination request. The
  current workflow leaves the primary action disabled and provides no retry.
- The next priority is state communication for keyboard and screen-reader users.

## P1 findings

### Coordination failure has no in-context recovery

- **Location:** `frontend/app.js:269-274`
- **Category:** Accessibility / interaction
- **Impact:** A network or API failure hides the brief, leaves the coordinate
  button disabled, and provides no retry action. The user must reload the page
  and loses their place.
- **Standard:** WCAG 2.2, 3.3.3 Error Suggestion; resilient task completion.
- **Recommendation:** Preserve or restore the brief and expose a keyboard-
  reachable `Try coordination again` action with an idempotent request.
- **Suggested command:** `impeccable harden`

### Coordination progress changes are visual-only

- **Location:** `frontend/index.html:63-68`, `frontend/app.js:251-259`
- **Category:** Accessibility
- **Impact:** The list has `aria-live`, but its text never changes when items
  become active or complete. Screen-reader users do not receive meaningful
  progress updates.
- **Standard:** WCAG 2.2, 4.1.3 Status Messages.
- **Recommendation:** Add textual state per item and `aria-busy` on the
  coordination region. Announce one concise completion status at a time.
- **Suggested command:** `impeccable harden`

### Focus does not move to revealed issues

- **Location:** `frontend/index.html:73`, `frontend/app.js:268`
- **Category:** Accessibility
- **Impact:** Calling `focus()` on a non-focusable heading has no effect, so
  keyboard and screen-reader users remain at a control that is now hidden.
- **Standard:** WCAG 2.2, 2.4.3 Focus Order.
- **Recommendation:** Give the issues heading `tabindex="-1"` and focus it after
  revealing the section, as already done for the agenda heading.
- **Suggested command:** `impeccable harden`

### Failure states retain success styling

- **Location:** `frontend/styles.css:48-51`, `frontend/app.js:66-83`
- **Category:** Theming / accessibility
- **Impact:** `Plan needs review`, expired authorization, and unknown reservation
  status continue to use the green success band and dot. Text prevents a
  color-only failure, but the visual semantics conflict with the message.
- **Standard:** WCAG 2.2, 3.2.4 Consistent Identification.
- **Recommendation:** Add neutral, warning, and error state modifiers with text,
  border, background, and icon/dot tokens. Apply them from one status helper.
- **Suggested command:** `impeccable colorize`

## P2 findings

### Disabled Edit plan advertises an unavailable critical action

- **Location:** `frontend/index.html:114`
- **Category:** Interaction / anti-pattern
- **Impact:** The user flow promises edits invalidate authorization, but the only
  edit control is permanently disabled. This exposes prototype scaffolding at
  the main decision boundary.
- **Recommendation:** Implement scoped plan editing and authorization
  invalidation, or remove the control from the release demo.
- **Suggested command:** `impeccable craft`

### Several text buttons have small touch targets

- **Location:** `frontend/styles.css:52`, `frontend/index.html:93,175`
- **Category:** Responsive / accessibility
- **Impact:** Evidence and authorization-record controls can be difficult to tap
  on phones or for users with motor impairments.
- **Standard:** WCAG 2.2, 2.5.8 Target Size (Minimum).
- **Recommendation:** Give interactive text controls a minimum 44 by 44 px hit
  area without making their visual treatment heavy.
- **Suggested command:** `impeccable adapt`

### Coordination trace waits for the response before showing activity

- **Location:** `frontend/app.js:242-259`
- **Category:** Performance perception
- **Impact:** A slow Gemini request leaves four static waiting rows for the full
  network duration, then plays a synthetic completion sequence afterward.
- **Recommendation:** Mark the first step active immediately and update bounded,
  truthful phases as backend events become available. Do not imply tool timing
  that was not observed.
- **Suggested command:** `impeccable optimize`

### Copy feedback is not a dedicated status message

- **Location:** `frontend/app.js:371-377`
- **Category:** Accessibility
- **Impact:** Replacing the button label may be missed by assistive technology
  and provides no stable outcome text.
- **Standard:** WCAG 2.2, 4.1.3 Status Messages.
- **Recommendation:** Announce copy success or failure in the existing status
  region and restore the button label after a short bounded interval.
- **Suggested command:** `impeccable harden`

## P3 finding

### Product heading uses a marketing-style fluid scale

- **Location:** `frontend/styles.css:33`
- **Category:** Typography
- **Impact:** The large fluid heading is attractive but slightly overstates the
  hero relative to a focused operations tool.
- **Recommendation:** Replace it with a fixed product-scale heading and use
  structural spacing for responsive adaptation.
- **Suggested command:** `impeccable typeset`

## Patterns and systemic issues

- Dynamic workflow states are distributed across event handlers rather than a
  single state-rendering function. This causes semantic styling and focus
  behavior to drift.
- Success has dedicated tokens, while warning, error, and informational states
  do not.
- `DESIGN.md` is missing, so established tokens, component states, and responsive
  rules are not yet recorded as a reusable contract.

## Positive findings

- Semantic landmarks, headings, buttons, labels, and disclosure relationships
  are used consistently.
- Visible focus is strong and reduced-motion preferences are respected.
- Proposal, authorization, and reservation are unmistakably separate states.
- The UI never implies a real reservation before explicit human action.
- Layout breakpoints collapse the plan, authorization, ledger, and handoff in a
  structurally coherent order.
- The frontend has no framework or third-party runtime, keeping delivery lean.
- The OKLCH palette passes measured AA contrast for all active text combinations
  inspected.

## Recommended actions

1. **P1 `impeccable harden`:** Repair coordination retry, focus movement,
   progress announcements, and copy feedback.
2. **P1 `impeccable colorize`:** Add semantic status variants and centralize
   state rendering.
3. **P2 `impeccable craft`:** Implement edit-and-reauthorize or remove the
   unfinished control.
4. **P2 `impeccable adapt`:** Bring text-control hit areas to 44 px.
5. **P3 `impeccable document`:** Capture the established design system in
   `DESIGN.md`.
6. **P3 `impeccable polish`:** Run the final integrated quality pass.

Re-run the Impeccable audit after fixes to measure improvement.
