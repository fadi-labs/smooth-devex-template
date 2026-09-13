---
description: 'Clean Code baseline (Robert C. Martin) — intent-revealing names, one-thing functions, self-documenting code over comments, tell don''t ask, Boy Scout Rule'
globs: "**"
paths:
  - "**"
applyTo: '**'
alwaysApply: true
---

# Clean Code

Cross-cutting craftsmanship baseline distilled from Robert C. Martin's _Clean Code_. C# collection
shape (array vs `List`) lives in [`backend/readonly-collections`](backend/readonly-collections.instructions.md).

## Names

- Name reveals **intent** — `deleteItems`, not `bustThemDown`. Pronounceable and searchable; no
  single-letter or `foo`-style names for anything with lifetime beyond a loop.
- **No type or container in the name** — `name`, not `nameString`; `events`, not `eventsList`.
- Classes/types are **nouns**, methods/functions are **verbs**.
- Use domain and pattern vocabulary the next engineer already knows (`EmployeeFactory`, `RecipeVersion`).
- Rename a bad name when you touch it and the rename stays inside the change's blast radius.

## Functions

- **Small.** Do **one thing** at one **level of abstraction** — a name needing `And` means split it.
- Fewest arguments that work; no boolean flag argument that selects between two behaviours (split it).
- No hidden side effects: a function either answers a question or changes state, not both.
- Extract each step of a multi-step computation into a named function instead of reassigning one
  accumulator variable.

## Comments

- **No comments unless the user explicitly asks** ([`code-review-standards`](code-review-standards.instructions.md)
  Code Comments Policy). Do not add one to justify code that is hard to read — rename or extract instead.
- When a comment *is* requested, it states the **why** (deliberate ordering, external-system
  workaround), never the what, in one line.
- Never leave commented-out code, changelog comments, or banner blocks. Delete them.

## Layout

- Formatting is owned by `.editorconfig` — never hand-format, never review it
  (see [`code-review-standards`](code-review-standards.instructions.md)).
- What tools can't enforce: **blank lines separate concepts** (vertical openness); declare a variable
  **adjacent to its first use**; order a file top-down — entry points first, their helpers below.

## Data, objects, coupling

- **Objects hide their internals and expose behaviour; data structures expose their fields and carry no
  behaviour.** Both are valid — pick one per type, deliberately. The shape to avoid is the **mutable
  hybrid**: settable state *plus* rules about that state, so an invariant holds only while callers
  remember to go through the method. An immutable type carrying behaviour (value object, strongly typed
  ID) is an object, not a hybrid.
- **Law of Demeter — one dot.** Prefer `a.DoThing()` over `a.B.C.DoThing()`; reaching through a chain
  couples you to internals. Chained fluent builders and LINQ/array pipelines are not violations.
- Avoid `null` in and out of your own APIs. Model absence explicitly (`Result<T>`, optional
  parameter, discriminated union).
- Duplication is the root smell: extract on the **second** occurrence when both call sites change for
  the same reason, not when they merely look alike.

## Practice

- **Boy Scout Rule** — leave touched code cleaner than you found it, in small increments inside the
  change's scope. Cleanup that grows the diff beyond the task belongs in its own change.
- Clean code is testable code. If a unit is hard to test, that's a design defect, not a test problem.

## Changelog

> AI loading note: Skip this section during routine task execution. Use it only when updating this rule file.

| Date | Change |
|:-----|:-------|
| 2026-09-13 | Copied from gf-recipe-editor; retargeted comments policy and dropped missing per-stack links. |
| 2026-09-13 | Linked `backend/readonly-collections` for array vs `List`. |
