# {{TITLE}} — High-Level Design

| | |
|---|---|
| **Status** | In Discovery |
| **Owner** | <team / handle> |
| **Tracker** | [<project / epic name>](<url>) |
| **Last updated** | {{DATE}} |

> Discovery / prototyping HLD. This document delivers **intent + spec** — what we are
> building and why, the decisions behind it, and the quality bar it must meet. It does
> **not** contain an implementation plan; execution (phasing, sub-issues, sequencing) is
> tracked in the issue/work tracker.
>
> Requirements state the *outcome* and its constraints. Where a mechanism is named, it is because
> choosing differently breaks a decision — everything else is the implementer's call.

<!-- Budget ~1500 words total; ≤ 150 words per goal before its acceptance criteria. Over budget
     means cut, not reformat. -->

## Intent

<2–4 sentences. What is being introduced and why now. State the problem and the
target outcome. No marketing language.>

## Key Goals

### 1. <Goal>

<1–2 short paragraphs: the change and the principle behind it. Concrete beats abstract. Do not
describe how to build it.>

**Acceptance criteria / DoD**

- <Observable, testable condition that means this goal is met.>
- <Another condition. These are the design's definition-of-done, not test cases.>

### 2. <Goal>

<...>

**Acceptance criteria / DoD**

- <...>

## Core Separation of Concerns

> <One blockquoted thesis sentence — the load-bearing premise the design rests on.>

<1–2 paragraphs expanding the thesis.>

## Guiding Principle — <Tagline>

> <One blockquoted slogan.>

- <Ownership / independence rule.>
- <What we will deliberately NOT do.>

---

## Diagrams

- [System Context (C1) + supporting diagrams](./diagrams/c4-context.md)

## Architecture Decisions (LADRs)

LADRs 01–N are strategic (*what* and *why*); later LADRs are tactical (*how*). Each is a small, local
decision the design actually forces — if the goals do not conflict on a point, it is a detail, not a
decision. See [`./ladrs/`](./ladrs/).

| LADR | Decision | Status |
|------|----------|--------|
| [LADR-01](./ladrs/LADR-01-example.md) | <Title — one-line summary> | Draft |

## Non-Functional Requirements

Only quality concerns **this** design puts an unusual demand on — concerns already bound by a
documented repo rule or ADR (e.g. logging conventions, secrets hygiene) are not repeated here. Each
carries a measurable target, a verification mechanism, and acceptance criteria. See [`./nfrs/`](./nfrs/).

| NFR | Attribute | Target (summary) | Status |
|-----|-----------|------------------|--------|
| [NFR-01](./nfrs/NFR-01-example.md) | <Attribute> | <measurable target> | Draft |
