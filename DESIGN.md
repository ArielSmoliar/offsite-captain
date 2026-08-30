---
name: Offsite Captain
description: A calm operating workspace for planning and authorizing startup offsites.
colors:
  ink: "oklch(24% 0.018 70)"
  muted: "oklch(49% 0.018 70)"
  paper: "oklch(98% 0.008 82)"
  surface: "oklch(99.5% 0.004 82)"
  line: "oklch(88% 0.014 76)"
  terracotta: "oklch(47% 0.11 42)"
  terracotta-hover: "oklch(41% 0.11 42)"
  terracotta-soft: "oklch(94% 0.03 55)"
  success: "oklch(45% 0.09 151)"
  success-soft: "oklch(95% 0.025 151)"
  info: "oklch(43% 0.08 245)"
  info-soft: "oklch(95% 0.025 245)"
  warning: "oklch(42% 0.085 72)"
  warning-soft: "oklch(95% 0.03 78)"
  focus: "oklch(55% 0.16 252)"
typography:
  display:
    fontFamily: "Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "3.25rem"
    fontWeight: 700
    lineHeight: 1.02
    letterSpacing: "-0.045em"
  headline:
    fontFamily: "Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "1.35rem"
    fontWeight: 700
    lineHeight: 1.2
  body:
    fontFamily: "Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "0.74rem"
    fontWeight: 760
    lineHeight: 1.2
    letterSpacing: "0.1em"
rounded:
  control: "0.5rem"
  panel: "0.75rem"
  feature: "0.9rem"
spacing:
  xs: "0.5rem"
  sm: "0.75rem"
  md: "1rem"
  lg: "1.5rem"
  xl: "2.5rem"
components:
  button-primary:
    backgroundColor: "{colors.terracotta}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "0.7rem 1rem"
    height: "3rem"
  button-primary-hover:
    backgroundColor: "{colors.terracotta-hover}"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "0.7rem 1rem"
    height: "3rem"
  text-action:
    backgroundColor: "transparent"
    textColor: "{colors.terracotta}"
    padding: "0.65rem 0.25rem"
    height: "2.75rem"
---

# Design System: Offsite Captain

## Overview

**Creative North Star: "The Operations Run Sheet"**

Offsite Captain should feel like the clean, annotated run sheet a trusted chief
of staff brings into a high-stakes planning meeting. Information is calm and
ordered, state changes are explicit, and the plan remains the primary object.
The interface uses a warm paper field, disciplined rules, and one restrained
terracotta action color rather than dashboard ornament.

The system rejects chat-first experiences, repeated-card SaaS dashboards,
travel-marketplace urgency, unexplained AI output, false reservation certainty,
decorative motion, novelty controls, and technical detail that obscures a
decision. Motion communicates state only. Desktop layouts show useful context
side by side; narrow layouts preserve the same workflow in one column.

**Key Characteristics:**

- Calm, precise, and accountable
- Editorial structure with product-native controls
- Restrained color with unmistakable semantic states
- Explicit separation of proposal, authorization, and reservation

## Colors

Warm neutral surfaces keep long planning sessions comfortable. Terracotta marks
primary actions and current state; green, blue, and ochre communicate success,
information, and warning without relying on color alone.

### Primary

- **Decision Terracotta:** Reserved for primary actions, current workflow state,
  and terse emphasis. It is never decorative.

### Neutral

- **Run-Sheet Ink:** Primary text and structural rules.
- **Warm Paper:** The persistent workspace background.
- **Clean Surface:** Raised authorization and confirmation surfaces.
- **Pencil Gray:** Secondary text, supporting metadata, and inactive state.
- **Ledger Line:** Dividers and quiet component boundaries.

### Named Rules

**The One Decision Rule.** Terracotta occupies no more than ten percent of a
screen and always points to the next consequential action.

**The Text Plus Color Rule.** Every semantic color is paired with a title,
status message, or state label.

## Typography

**Display Font:** Inter with the native sans-serif stack  
**Body Font:** Inter with the native sans-serif stack  
**Label/Mono Font:** The same sans-serif family; native monospace is reserved for
plan hashes and identifiers.

**Character:** One familiar, carefully tuned sans family lets the interface
disappear into the work. Weight, scale, spacing, and case establish hierarchy.

### Hierarchy

- **Display** (700, 3.25rem, 1.02): The single page title on desktop; 2.45rem on
  narrow screens.
- **Headline** (700, 1.35rem, 1.2): Major workflow sections.
- **Title** (700, 0.98rem, normal): Sessions, commitments, and handoff groups.
- **Body** (400, 1rem, 1.6): Explanations and decision copy, capped near 65ch.
- **Label** (760, 0.74rem, 0.1em, uppercase): Eyebrows and operational metadata.

### Named Rules

**The Fixed Product Scale Rule.** Product headings use fixed rem sizes with one
mobile adjustment. Fluid marketing typography is prohibited.

## Elevation

The system is flat by default. Borders, warm tonal layers, and whitespace carry
most depth. A single diffuse ambient shadow is reserved for the authorization
surface, where the operator crosses a consequential boundary.

### Shadow Vocabulary

- **Authorization lift** (`0 18px 50px oklch(30% 0.02 70 / 0.09)`): Use only on
  the exact-scope approval surface.

### Named Rules

**The Earned Elevation Rule.** A surface receives shadow only when its decision
weight is greater than its surroundings.

## Components

### Buttons

- **Shape:** Compact, gently curved controls (0.5rem radius) with at least a
  44px touch target.
- **Primary:** Terracotta fill, clean-surface text, and a 3rem minimum height.
- **Hover / Focus:** Darken on hover; use a visible 3px blue focus outline and a
  restrained 180ms ease-out state transition.
- **Secondary / Ghost:** Transparent surface, structural border where needed,
  and identical geometry to the primary action.

### Chips

- **Style:** Small semantic tags use a soft tonal background and matching dark
  text. They label content and never masquerade as buttons.

### Cards / Containers

- **Corner Style:** Most content uses open sections and horizontal rules. Only
  status, authorization, and confirmation regions receive rounded containers.
- **Background:** Warm paper at rest; clean surface for consequential boundaries.
- **Shadow Strategy:** Flat except for the authorization surface.
- **Border:** One-pixel Ledger Line or semantic-state border.
- **Internal Padding:** 1.2rem for status, 2.5rem for decision surfaces, and
  1.4rem for those surfaces on small screens.

### Inputs / Fields

- **Style:** Native, familiar controls with the same 0.5rem corner vocabulary.
- **Focus:** A 3px blue outline with a 3px offset.
- **Error / Disabled:** Text explains the state; muted treatment never removes
  legibility.

### Navigation

The top bar identifies the product and demo context. A numbered horizontal
workflow shows completed, current, and future steps; it remains scrollable on
narrow screens rather than changing the information architecture.

### Coordination Trace

The trace is a semantic ordered list. It exposes Waiting, In progress, and
Complete as text. It never plays synthetic tool timing after the backend result.

## Do's and Don'ts

### Do:

- **Do** make the operating plan the primary object and keep explanatory prose
  near 65 characters per line.
- **Do** keep every text action at least 44px high and every focus state visible.
- **Do** label proposal, authorization, and reservation as separate states.
- **Do** use restrained motion only for direct state feedback between 150ms and
  250ms.
- **Do** treat dietary and accessibility needs as operational requirements.

### Don't:

- **Don't** build chat-first experiences that hide the plan, constraints, or
  current state in a transcript.
- **Don't** use generic SaaS dashboards made from repeated cards without a
  workflow hierarchy.
- **Don't** imitate travel marketplaces that prioritize browsing, promotions,
  or urgency tactics.
- **Don't** present unexplained AI output, false certainty, or language implying
  reservations exist before human authorization.
- **Don't** use decorative motion, novelty controls, or dense technical detail
  that distracts from the operator's decision.
- **Don't** use gradient text, glassmorphism, colored side stripes, or nested
  cards.
