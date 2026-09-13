# Task shape

Every Task drafted by this skill follows this shape. Keep it terse — cut before you pad.

```markdown
## Goal
One or two sentences: what this delivers and why, in plain language a developer can act on
without re-reading the Feature.

## Depends on
Either a real reference ("S2.1", "#42") or "None — can start immediately." If dependent on
more than one thing, list all of them; each one also needs a matching GitHub `blocked_by` link
once written.

## Acceptance criteria
- One bullet per testable condition. Cite the source ID in parentheses when translating a
  requirement: "Repeat lookups inside a minute are served from cache (NFR-13)."
- Preserve measurable bars exactly as stated in the source — don't soften "p95 < 5s" into
  "acceptable performance."
- Any technology mention reads as a non-binding example: "For example with tech stack: X — team's
  call, not fixed by this Task."

## Known issues to carry into implementation (only if applicable)
Anything flagged as an open question or known risk at the Feature level that now specifically lands
on this Task. Don't let a restructure quietly drop these.

## Out of scope
What this Task explicitly does not cover, especially anything a reader might otherwise assume is
included (adjacent Tasks, deferred work, out-of-scope items inherited from the Feature).

## Translation (AI context)

| Role | GitHub | Notes |
|------|--------|-------|
| Initiative | **Project** | Existing GitHub Project. Do not create a Project. |
| Epic | **Feature** issue (`--type Feature`) | Top-level. No parent unless the user gives one. |
| Story | **Task** issue (`--type Task`) | Sub-issue of the Feature. FR/NFR → acceptance criteria. |
| Subtask | Untyped issue (no `--type`) | Out of scope here. `agile-github-task-from-diff` later. |
```

## Naming

- Flat sequential numbering (`S1`, `S2`, `S3`, ...) is the default.
- Sub-numbering (`S2.1`/`S2.2`) is reserved for a stub→consumer pair: a Task built specifically so
  another Task can be developed or tested against it before real access/data exists. `.1` is the
  stub/prerequisite, `.2` is the consumer that depends on it.
- Don't renumber existing, already-created Tasks without previewing the rename to the user first
  — a GitHub title rename is a visible change to shared state.

## Dependency graph, not a line

Before assigning any numbers, sketch (even just in prose) which Tasks:
- can start immediately (no dependency),
- are strictly blocked by another Task,
- are independent of each other even though they'll be discussed together (e.g. two stub Tasks
  for two different upstream APIs — similar shape, no dependency between them).

Only Tasks on the same blocking chain get sequential numbers implying order. Two independent
Tasks should not be numbered as if one must finish before the other starts.
