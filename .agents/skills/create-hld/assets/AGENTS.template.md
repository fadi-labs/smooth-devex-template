# AGENTS.md - {{TITLE}}

AI Context: HLD for {{TITLE}}. Updated: {{DATE}}

> AI-coder context for this HLD. Architecture diagrams live in [`./diagrams/`](./diagrams/),
> decisions in [`./ladrs/`](./ladrs/), quality spec in [`./nfrs/`](./nfrs/). This file is
> guardrails, not narrative — the narrative is in [`./README.md`](./README.md).

<!-- Budget ~700 words. Every line must stop a wrong decision. Do not restate project-wide standards
     that repo rules and ADRs already enforce, and do not prescribe a mechanism unless a different
     one would violate an LADR. -->

## TL;DR

<One line: what this HLD covers + where intent, decisions, and quality spec live.>

## Non-Negotiables

- <Thing an AI coder building against this design would plausibly get wrong — specific to THIS design.>
- LADRs are Draft/Prototype status — flag deviations rather than silently overriding.

## Architecture Decisions

Only decisions whose violation produces wrong code. Full records in [`./ladrs/`](./ladrs/).

| LADR | Decision | Why it matters |
|------|----------|----------------|
| LADR-01 | <decision> | <consequence of getting it wrong> |

## Key Behaviors

- <Non-obvious runtime/operational truth not apparent from a design read.>

## Quality Constraints

Measurable NFRs live in [`./nfrs/`](./nfrs/). Constraints that change how code is written:

- <e.g. tenant isolation rule, key-ownership boundary — not a duplicated NFR target.>

## Changelog

| Date | Change | Ref |
| :---- | :---- | :---- |
| {{DATE}} | HLD scaffolded | <ticket> |
