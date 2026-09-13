---
name: agile-github-breakdown
description: >
    Invoke to turn a clarified braindump, meeting, or existing GitHub Feature into terse
    Feature + Task content — FR/NFR translated into acceptance criteria, an explicit
    dependency graph, soft technology suggestions, and GitHub writes gated behind a
    dry-run preview. Trigger keywords: "create stories", "break this epic down",
    "produce stories for", "turn this braindump into a feature", "agile github breakdown".
    Also triggers on /agile-github-breakdown. Complements ai-brain-dump (run after its
    synthesize step) and shares GitHub Project / sub-issue / gh conventions with
    agile-github-task-from-diff — but that skill sources an untyped subtask from a git
    diff; this one sources Feature + Task issues from contextual knowledge (braindumps,
    transcripts, existing Features), never a diff.
allowed-tools: >
    Bash(.agents/skills/agile-github-breakdown/scripts/parse_frnfr.py:*),
    Bash(.agents/skills/agile-github-breakdown/scripts/validate_story_graph.py:*),
    Bash(.agents/skills/agile-github-breakdown/scripts/create_github_breakdown.py:*),
    Bash(gh issue view:*),
    Bash(gh api:*),
    Read, Write, Edit
models:
  claude: opus        # high-complexity; multi-step clarification + dependency-graph judgment
  copilot: auto
  codex: gpt-5.5
---

# Create Feature — braindump/epic → GitHub Tasks

## TL;DR

Take a clarified set of requirements (a braindump synthesis, a meeting transcript, or an existing
GitHub Feature's FR/NFR table) and produce terse Task content: one Task per cohesive deliverable,
an explicit dependency graph, every FR/NFR translated into a checkable acceptance criterion, every
technology mention phrased as a non-binding example. Preview before writing; write to GitHub only
on explicit go-ahead.

Vanilla GitHub issue types only: **Feature** (epic) and **Task** (story). Never create an org issue
type. The GitHub Project is the initiative — do not create a Project.

Write it **terse and structural**. A Task a developer can act on without re-reading the Feature
beats one that restates it. Leave the implementer room to choose *how*.

## Translation (AI context)

This table **must** appear in every Feature and Task body this skill writes. `create_github_breakdown.py`
appends it if missing. Keep it so later agents map Jira-shaped language onto GitHub without inventing
an Epic type.

| Role | GitHub | Notes |
|------|--------|-------|
| Initiative | **Project** | Existing GitHub Project (`--project`, default `1`). Do not create a Project. |
| Epic | **Feature** issue (`--type Feature`) | Top-level. No parent unless the user gives one. |
| Story | **Task** issue (`--type Task`) | Sub-issue of the Feature. FR/NFR → acceptance criteria. Graph via `blocked_by`. |
| Subtask | Untyped issue (no `--type`) | Out of scope here. `agile-github-task-from-diff` later. |

Do not create org issue types. Stock types are Task / Bug / Feature only. Creating an Epic type is
an org-admin side effect (`admin:org`) and still does not give Projects an Epic container.

Reference graph: `generic-automation-and-it/builder-catalogue` — Project (initiative) → Feature #1
(epic) → Task #2 (story) → untyped #21 (subtask).

## Non-Negotiables

- **Dry run before any GitHub write.** Default to previewing drafted/changed content — new Tasks,
  Feature body edits, sub-issue links, `blocked_by` links — and wait for explicit go-ahead. Only skip
  the preview if the user's current request already says "do it" / "create them" unambiguously.
  `create_github_breakdown.py` is dry-run unless `--apply` is passed.
- **Never delete a live GitHub issue as part of a restructure.** Close, or leave it and link
  (`blocked_by` / Relates via body), instead. If asked whether to delete something, recommend against
  it and explain why before acting.
- **Stories are GitHub `Task`, not `Feature` and not untyped.** This skill's children are the story
  layer. Untyped issues are subtasks for `agile-github-task-from-diff`. Don't default to Feature just
  because the source material is called an "epic".
- **Never create an issue type.** Feature and Task already exist on a vanilla org. An Epic type is
  out of scope even if the API can add one.
- **Every FR/NFR assigned to a Task becomes a checkable AC bullet citing its ID.** Preserve
  measurable bars verbatim — "p95 < 5s" stays "p95 < 5s", never softened to "acceptable performance".
  Do not invent requirements that aren't traceable to the source material.
- **Every technology mention is a soft suggestion, never a requirement**, unless the source material
  explicitly mandates it. Phrasing: *"For example with tech stack: X — team's call, not fixed by this
  Task/Feature."* This applies even when discussing implementation approaches the team already leans
  toward — the Feature states outcomes, not mechanisms.
- **Dependencies are a graph, not a sequence.** Two Tasks that don't block each other stay parallel
  even if numbered consecutively. When one Task is a prerequisite consumed by exactly one other
  (e.g. a stub built so a client can be tested against it), use sub-numbering (`S2.1`/`S2.2`) rather
  than inflating the flat sequence — this keeps stub↔consumer pairs visually grouped.
- **State every dependency as prose AND as a GitHub `blocked_by` link.** "Depends on: S2.1" in a
  description is not enough — create the dependency too, so the graph survives outside this
  conversation.
- **Carry known issues and open questions forward, don't drop them on a restructure.** If splitting a
  Task moves an FR/NFR or a flagged risk to a different Task, the receiving Task's description
  must say so explicitly.
- **Clarify before inventing.** Target Feature (existing `#n` or new), project (default `1`,
  override with `--project`), live-vs-dry-run intent, and whether a local knowledge-doc mirror exists
  — ask, do not assume.
- **Local knowledge-doc mirror is opt-in, never invented unprompted.** If a `.context/*-context.md`
  (or equivalent) file already tracks this Feature, keep it in sync with the same edits. If none
  exists, ask whether to create one before writing it — it's a workspace convenience, not a universal
  requirement, and not every host running this skill has that convention.

## Inputs

| Flag | Default | Description |
|------|---------|-------------|
| `--project` | `1` | GitHub Project number under the org (the initiative). Override for any other project. |
| `--org` | _(repo owner)_ | GitHub org that owns the project. Defaults to the repo owner detected from the git remote. |
| `--feature-issue` | _(none)_ | Existing Feature to attach Tasks under — number, `#n`, or issue URL. Omit to create a new Feature. |
| `--no-project` | — | Create the issues only; skip adding them to any GitHub Project. |
| `--apply` | — | Write to GitHub. Default is dry-run preview. |

## Workflow

1. **Clarify scope** — target Feature (GitHub `#n`, or "new"), project (default `1`, override with
   `--project`), and whether the user wants a dry run or has already authorized live creation. Do
   not assume a parent for a new Feature — Features are top-level. Do not create a Project.
2. **Gather source material** — load the Feature via `gh issue view` and/or the local context
   doc if the user points at one. You now hold the body, so **extract the FR/NFR rows yourself**
   and hand them to `scripts/parse_frnfr.py --prefix FR NFR` as an explicit list, one per
   line:

   ```
   FR-1 | The system must accept a line recipe payload
   NFR-11 | p95 < 5s for a single recipe read
   ```

   The script validates, filters, de-duplicates, sorts numerically (`FR-10` after `FR-9`) and emits
   the JSON that step 6 feeds to the validator — the parts that are tedious and error-prone by hand.
   It deliberately does **not** parse Markdown: it used to hunt for tables inside the raw body,
   and that made the whole GFM/CommonMark spec its input surface. Copy the rows across instead; you
   already have them in context, and any line the script cannot read is a hard error naming the line
   number rather than a silent omission. **Always pass `--prefix FR NFR`** (or whatever prefixes the
   Feature uses) so a stray issue number like `#42` cannot be mistaken for a requirement. If working
   from a meeting transcript, flag reliability caveats (e.g. single-microphone recordings can't
   reliably attribute quotes to a speaker) rather than presenting attributed quotes as fact.
3. **Structure the dependency graph** — list candidate Tasks with what each delivers and what it
   depends on. Draw it as a graph first (even mentally): which Tasks can start immediately, which
   are blocked, which are parallel-but-unrelated.
4. **Translate FR/NFR → AC** — for every requirement a Task owns, write one AC bullet: the testable
   condition, then the source ID in parentheses.
5. **Draft each Task** — Goal, Depends on, Acceptance criteria, Out of scope (see
   `references/story-template.md`). Fold in "Known issues to carry into implementation" wherever a
   Feature-level known issue or open question now lands on a specific Task. Include the translation
   table in every body.
6. **Validate, then preview** — build the `{requirement_ids, stories: [{key, depends_on, ac_ids}]}`
   JSON from steps 3–5 and run it through `scripts/validate_story_graph.py` (pass existing GitHub
   issue refs via `--known-external '#42'` so cross-references to already-created issues aren't
   flagged dangling). A non-zero exit (cycle, dangling dependency, duplicate story key, or an
   `ac_ids` entry citing a nonexistent requirement ID) is a hard stop — fix the graph before
   previewing to the user, don't relabel a fabricated ID as an intentional deviation.
   Missing-coverage and sub-numbering-suggestion warnings feed the draft: assign `N.1`/`N.2`
   where the script suggests a stub→consumer pair, and either cover every listed FR/NFR or flag why
   one is intentionally uncovered. Then show the user the full drafted/changed set: new Task
   content, any Feature body edits, the links to create, and the Feature-doc diff. Call out anything
   you're still assuming (e.g. "assuming S3.1 becomes independent of S2.2 — confirm").
7. **Write on go-ahead** — feed the draft to `scripts/create_github_breakdown.py --apply`:
   create/reuse the Feature (`--type Feature`), create every drafted Task (`--type Task`), add them
   to the Project, link Tasks as sub-issues of the Feature, set `blocked_by` for every "Depends on",
   then the local context-doc mirror if one exists. The script stamps the translation table and a
   Tasks key→`#n` table onto the Feature.
8. **Report** — list every created/changed issue with its URL. Flag anything still unresolved (open
   questions, duplicate-work risk between two similar Tasks) instead of quietly resolving it
   yourself.

If `gh` is unauthenticated, stop after the preview and hand back the drafted content instead of
guessing that the write succeeded.

## Quality bar before marking ready

- [ ] `scripts/validate_story_graph.py` ran clean: no cycles, no dangling `depends_on`, no duplicate
      story keys, no `ac_ids` entry citing a nonexistent requirement ID.
- [ ] Every entry in its `missing_coverage` output is either fixed (AC added) or explicitly noted as
      intentionally uncovered — never silently ignored.
- [ ] Every `subnumber_suggestions` pair was either adopted (`N.1`/`N.2`) or explicitly rejected with a
      reason.
- [ ] Every Task's AC bullets cite specific FR/NFR IDs, or the Task is explicitly marked as new
      work not traceable to the source.
- [ ] Every "Depends on" is either a real Task/issue reference or "None — can start immediately".
- [ ] Every dependency stated in prose has a matching GitHub `blocked_by` link.
- [ ] Every Feature and Task body includes the Translation (AI context) table.
- [ ] Every technology mention reads as an example, not a requirement.
- [ ] No Feature-level known issue or open question silently disappeared during the breakdown.
- [ ] Nothing was deleted from GitHub; superseded work is closed/linked, not removed.
- [ ] The user saw a preview and explicitly confirmed before any live GitHub write (`--apply`).
- [ ] If a local context-doc mirror exists, it was updated to match; if none exists, creating one was
      asked about, not assumed.

## Agent-agnostic notes

- `scripts/parse_frnfr.py` and `scripts/validate_story_graph.py` are `python3` stdlib only —
  no Claude-specific behaviour, no third-party deps. They handle the deterministic parts (ID
  extraction, cycle/dangling-reference detection, coverage diff, sub-numbering suggestion) so the
  agent isn't manually cross-referencing IDs by eye. The actual Task content (AC wording, which
  Tasks exist) stays agent judgment — there's no deterministic function for translating a
  requirement into English.
- `scripts/create_github_breakdown.py` owns `gh` argv (`shell=False`). The agent authors
  titles/bodies; the script creates Feature/Task, project-adds, sub-issue-links, and `blocked_by`.
- Composes with `ai-brain-dump`: that skill's Listen/Synthesize phases can feed this skill's Step 1
  input directly — this skill does not re-implement listen-first capture.
- Composes with `agile-github-task-from-diff`: that skill later creates **untyped** subtasks under a
  Task from a git diff. Do not collapse the two — same GitHub Task type is not used for both.

## References

- `references/story-template.md` — the Goal / Depends on / Acceptance criteria / Out of scope shape.
- `references/fr-nfr-translation.md` — the FR/NFR → AC translation rule and soft-tech-recommendation
  pattern, with a worked (anonymized) example.

## Scripts

- `scripts/parse_frnfr.py [file]` — normalise an **explicitly delimited** requirement list
  (one `<ID> | <text>` per line, from step 2) into JSON: strict validation with line numbers, prefix
  filtering, duplicate detection, numeric-aware sorting. Reads a file arg or stdin. **It does not
  parse Markdown** — do not pipe a raw Feature body at it. Exit 0 parsed, **exit 1** nothing matched
  (an empty list would pass every downstream coverage check), **exit 2** malformed input. `--prefix`
  requires at least one value. The ID must be bare (`FR-1`).
- `scripts/validate_story_graph.py [file] [--known-external KEY ...]` — validates a drafted Task
  graph: cycles, dangling `depends_on`, duplicate story keys, and an `ac_ids` entry citing a
  nonexistent requirement ID are all hard errors (exit 1); missing FR/NFR coverage and
  stub→consumer sub-numbering candidates are warnings in the JSON report. **Exit 2 is a malformed
  input**, not a failed graph. `stories` is required and `[]` is accepted, but **absence is not**.
  `requirement_ids` stays optional by contract. `requirement_ids`, `ac_ids` and `depends_on` must be
  **lists of strings**. Pass existing GitHub refs as `--known-external '#42'`.
- `scripts/create_github_breakdown.py [file] [--apply]` — create Feature + Tasks from a JSON
  payload `{feature: {title, body}, tasks: [{key, title, body, depends_on}]}`. Dry-run unless
  `--apply`. Stamps the translation table onto every body.
- `scripts/test_skill_scripts.py` — stdlib `unittest` regression suite for parse/validate. Run after
  touching either script:
  `python3 .agents/skills/agile-github-breakdown/scripts/test_skill_scripts.py` — `unittest discover`
  cannot be used, `.agents` is not an importable path segment.

## Changelog

| Date | Change | Ref |
| :---- | :---- | :---- |
| 2026-09-13 | Ported from `epic-breakdown` (Jira) onto vanilla GitHub Projects: Feature = epic, Task = story, Project = initiative, untyped sub-issue = subtask. Translation table required on every issue body. | — |
