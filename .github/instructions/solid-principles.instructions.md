---
description: 'When SOLID is a real diagnosis and when applying it makes the code worse — premature abstraction, ADR precedence, the triggers worth acting on'
globs: "**"
paths:
  - "**"
applyTo: '**'
alwaysApply: true
---

# SOLID Principles

The principles need no restating. What follows is when one is a real diagnosis here, and when
applying it makes the code worse.

## Apply on demand, not on sight

- SOLID diagnoses code that is **already hard to change**. An abstraction added for one caller is
  indirection, not design. Name the concrete pain — a `switch` you must edit again, an interface you
  must stub members of — or write the direct code.
- **Never refactor working code to "be SOLID."** Cleanup rides inside the change's blast radius.
- Where a principle conflicts with an ADR, the **ADR wins** — say so, do not silently comply. A
  `*Service` layer is the standard SOLID-trained instinct;
  [`backend/architecture-slices`](backend/architecture-slices.instructions.md) organises Application
  as vertical-slice features, not a service layer.

## Triggers worth acting on

- **Second case, not first.** A `switch` or `if`/`else if` ladder keyed on a type, enum or
  discriminator earns an abstraction on its second case, not its first. The ladder is the obvious
  shape, not the only one — the same key branched on in two files, or one new variant forcing edits to
  a factory *and* a mapper *and* a validator, is the same trigger and a worse one.
- **Complexity measured as change cost.** Count the places one behavioural change has to touch, or
  the unrelated reasons one file keeps getting edited for. Line count and nesting depth are Clean
  Code's concern, not a SOLID diagnosis — and "this feels complex" is not a measure at all: it
  licenses exactly the premature abstraction above.
- **A test forced to stub members it does not exercise** means the interface is too wide. Split it —
  never satisfy an unused member with a throw.

Once a trigger has fired, reach for the pattern already in this codebase (keyed registry, factory via
DI, named constructor, decorator). Do not invent a new abstraction family on first sight.

## Changelog

> AI loading note: Skip this section during routine task execution. Use it only when updating this rule file.

| Date | Change |
|:-----|:-------|
| 2026-09-13 | Copied from gf-dynamic-pallet-position; retargeted Service-layer ban to architecture-slices. |
