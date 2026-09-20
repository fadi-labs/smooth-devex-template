---
name: create-worktask
description: >
    Invoke to scaffold and fully populate a worktask under `.context/work-tasks/`
    so a standalone AI coder can execute it without asking questions. Trigger
    keywords: "create worktask", "create a work task", "make a work-task",
    "promote this to a worktask". Also triggers on /create-worktask.
    Does NOT trigger on questions about how worktasks work.
allowed-tools: >
    Bash(.agents/skills/create-worktask/scripts/scaffold-worktask.sh:*),
    Read, Write, Edit, Glob, Grep
models:
  claude: opus        # high-complexity; investigation + requirement authoring the whole 9-phase workflow runs on
  copilot: auto
  codex: gpt-5.5
---

# Create Worktask — standalone task authoring

## TL;DR

Produce `.context/work-tasks/<slug>.md` carrying **Title, Execution Profile, Contexts, Instructions**
and (only when needed) **Overrides**. The worktask *links* the process manual
(`.agents/templates/AI_WORKTASK_PROMOTE_STANDALONE_TEMPLATE.md`) — it never copies it.

The worktask is the input the entire Odin→Bragi workflow runs on. Everything downstream inherits its
gaps, so populate it from **real investigation**, not placeholders.

## Non-Negotiables

- **Link the process manual, never copy it.** The template carries the phases, gates, output rules and
  Constraints block. Copying them into the worktask creates a second copy that drifts.
- **Contexts must be real, verified paths.** Open each one before listing it. A listed file that does
  not exist is worse than an omitted one — the executing session will hunt for it.
- **Acceptance criteria are testable and measurable.** "Works correctly" is not a criterion.
- **Commit permission is per-task and defaults to not allowed.** The Execution Profile's
  `Commits during execution` field is the only thing that grants it; `Push` is always `never`. Nothing
  in a worktask overrides `git-policy.instructions.md`.
- **The session model is a human action.** Recommend it; never claim to set it. The user runs
  `/model <name>` before starting and can switch at a gate.
- **No HTML comments in `assets/WORKTASK.template.md`.** The SkillSpector gate flags comments in skill
  assets as `P2` hidden instructions (see the `create-hld/assets/*` baseline entries). Authoring
  guidance lives here in SKILL.md instead, which is read every invocation. Reintroducing comments in
  the asset means adding a justified `.github/skillspector-baseline.yml` entry in the same PR.
- **Do not execute the worktask in the same turn that creates it.** Creating and executing are separate
  invocations; the user chooses the model and path in between.

## Invocation

`/create-worktask <kebab-slug>` — or describe the work in natural language and follow the workflow.

## Output structure (the contract)

```
.context/work-tasks/<kebab-slug>.md
├── # Task: <one-liner>
├── Process: link to AI_WORKTASK_PROMOTE_STANDALONE_TEMPLATE.md
├── ## Execution Profile   # model recommendation, path, subagents, commits, push
├── ## Contexts            # verified paths only
├── ## Instructions        # summary, acceptance criteria, requirements, scope,
│                          # integration points, NFRs, tests, dependencies
└── ## Overrides           # omit entirely when there are none
```

`.context/` is gitignored — worktasks are local, per-workspace, never committed.

## Workflow

1. **Understand the task** — parse the request and the conversation. If the intent is ambiguous in a way
   that changes what gets built, ask before scaffolding; do not invent requirements.

2. **Investigate before writing.** Batch the independent reads and greps in one message: candidate
   `*AGENTS.md` files, similar existing implementations, the rules and ADRs that apply, schema or API
   surfaces the change touches. This is what separates a usable worktask from a restated prompt.

3. **Scaffold** — run:
   ```bash
   .agents/skills/create-worktask/scripts/scaffold-worktask.sh <slug> [--title "One-liner"] [--force]
   ```
   It prints JSON of the created path. The slug is kebab-case and describes the task
   (`add-vessel-eta-validation`, `fix-claims-filter-bug`).

4. **Fill the Execution Profile:**
   - **Recommended session model + Path** — from the complexity read in step 7
   - **Subagents** — `none` unless the task genuinely needs read-only fan-out or worktree-isolated writers
   - **Commits during execution** — `not allowed` unless the user explicitly grants it for this task
   - **Push** — `never`

5. **Fill Contexts** — every resource a standalone coder needs, each one verified in step 2:
   - Domain/feature `*AGENTS.md` files governing the code being touched
   - ADRs and NFRs that apply (`.docs/hlds/`, `code-review-standards.instructions.md`)
   - Rule files that apply (logging conventions, git policy, workflow rules)
   - Root `AGENTS.md` for system context; existing similar features to follow
   - Schema / API surfaces where the change touches them
   - If no feature `*AGENTS.md` exists, say so and add "create `[domain]_AGENTS.md`" to Instructions

6. **Fill Instructions** — the phases downstream consume these:
   - **Summary + acceptance criteria + requirements + scope boundaries** (Phase 1 clarifies against these)
   - **Integration points, performance, security, compliance** (Phase 2 analyses these)
   - **Data model, API contracts, UI structure** where the change implies them (Phase 3 specifies these)
   - **Tests** — required tiers: L0 (unit) / L1 (component) / L2 (integration), and what each must cover
   - **Dependencies and references** — prior work, tickets/PRs, patterns to follow, known gotchas,
     migration path for breaking changes

7. **Recommend the session model and path** — a human action, reported to the user and recorded in the
   Execution Profile:
   - **Lightweight path (0→1→6→7→8)** with a fast model — config changes, single-file fixes,
     straightforward CRUD, <5 files, clear patterns
   - **Full path (0→1→2→3→4→5→6→7→8)** with a high-reasoning model — cross-cutting concerns,
     architectural decisions, ambiguous requirements, 5+ files, new patterns, complex integrations
   - One-line rationale. Remind the user to set it with `/model` before starting execution.

8. **Delete what does not apply** — remove unused placeholder bullets and drop `## Overrides` entirely
   when there are none. A worktask full of unfilled brackets reads as noise and hides the real content.

9. **Confirm** — show the file path, key acceptance criteria, files/domains affected, estimated
   complexity, and the recommended model + path.

## Quality bar before confirming

- [ ] Would a new AI coder execute this with only the worktask and its linked contexts?
- [ ] Does every listed context path exist? (Opened, not guessed.)
- [ ] Is every acceptance criterion testable and measurable?
- [ ] Are scope boundaries explicit — what is OUT as well as what is IN?
- [ ] Are the required test tiers named (L0/L1/L2) with what each must cover?
- [ ] Are dependencies and integration points concrete?
- [ ] Is the Execution Profile filled in — model, path, subagents, commits, push?
- [ ] Are all unfilled placeholder brackets gone?
- [ ] Does the worktask link the process template rather than restating its phases?

## Agent-agnostic notes

- The script is `bash` + coreutils only and finds the repo root via `git rev-parse` — Codex, Copilot
  and Cursor run it identically. It must stay executable (`chmod +x`).
- This skill replaced the `UserPromptSubmit` hook `.agents/hooks/worktask-create.sh` (removed
  2026-09-20), which only fired for Claude Code. Skill invocation works across all four runners.

## Changelog

| Date | Change | Ref |
| :---- | :---- | :---- |
| 2026-09-20 | Created — replaces the `worktask-create.sh` UserPromptSubmit hook. Carries the hook's remediated contract (Execution Profile; link-don't-copy; commits per-task and default not allowed; L0/L1/L2 tiers; model as a human action) plus a deterministic scaffolder and an asset template. | — |
