---
description: 'Rules vs Understandings — discovered knowledge is evidence, not orders; how to inherit it at task start and when to promote it'
globs: "**"
paths:
  - "**"
applyTo: '**'
alwaysApply: true
---

# Rules vs Understandings

This repository holds three kinds of knowledge. Confusing them is the failure this rule prevents.
Updated: 2026-09-20

| Kind | Where | Nature | Authority |
|------|-------|--------|-----------|
| **Rules** | `.agents/rules/` (→ `.github/instructions/`) | The user's decisions | Follow always |
| **AGENTS.md** | Nearest `*AGENTS.md` to the code | Functional intent, layered domain → sub-domain → feature → technology | Authoritative for that code |
| **Understandings** | `.context/understandings/<subject>-<yyyyMMdd-HHmm>/<slug>.md` | The **input and outcome** of a session's memory — reusable, and holding only what no code file or knowledge document already holds. A stamped folder is one export run; a slug repeated across folders is a version chain, newest current | Apply when the question matches one you are asking; **the newer of two conflicting units wins** |

**"Already holds" means the question, not the topic.** A document recording *what was decided* — an ADR,
an NFR, an LADR — has no claim on *how to recognise it, re-derive it, or choose again*. The verdict and
the reasoning that produces the verdict answer two different questions, so a document mentioning the
subject does not make the Understanding redundant.

**Rules are not up for reinterpretation** based on what you observe. If a rule appears to be causing
problems, say so — do not work around it.

**Understandings are evidence, not orders.** Apply one when its question matches, and say so when what
you observe contradicts it. They go stale, and a stale Understanding applied confidently is worse than
none at all.

**If a rule and an Understanding conflict, the rule wins** — and flag the conflict rather than
resolving it silently.

## Importing

At the start of a task, read `.context/understandings/INDEX.md` and load any Understanding whose
**question** matches one the work at hand will make you ask — or, where a unit carries no question, whose
**description** matches the work. Match first, read second: the index exists so that finding one
applicable Understanding does not cost the tokens of reading all of them.

The index groups Understandings by the subject they came out of, but match on **questions** — the work
that produced a piece of knowledge usually has nothing to do with the work it applies to.

Treat what you load as your own prior knowledge. The store is gitignored and per-workspace, so it may
be empty or absent — that is a normal state, not an error.

When nothing matches, say so — once, in a line. Silence is indistinguishable from not having looked.

**When two Understandings conflict, the newer wins** — decided by the folder stamp, falling back to
`updated`, whether they are versions of one slug or two slugs covering the same ground. `INDEX.md` already
resolves the version case: it lists the current copy of each slug only. Analyse briefly, note what changed
if it is material, and proceed with the newer; a conflict is not a blocker. **Ask when genuinely unsure** —
when the older carries evidence or a boundary the newer dropped, or the two disagree on something that
changes what you are about to do and recency alone does not settle it. Name both units, say what each
claims, recommend the newer, and do not silently pick.

When one contradicts what you observe, the system wins — recency decides between Understandings, not
between an Understanding and reality. Name the unit, say what you saw, and set its
`confidence: contested`. Do not delete it and do not quietly work around it.

Keep track of which loaded Understandings actually shaped the work. Loading is not inheriting — only what
changed what you did counts. When the session exports anything, those go in its `provenance.inherited` — the store's only signal for which knowledge is earning its
keep, and the only way to find what depended on a unit that later turns out to be wrong.

## Never export toolchain knowledge as an Understanding

The store is for knowledge about **the system being built** — domain behaviour, data and integration
constraints, performance and security characteristics. Knowledge about the **tools used to build it** —
skills, CI workflows, scanners, the agent harness, dependency versions — is not an Understanding, however
much it cost to learn. The skill you ran is never the subject: a braindump session is not an
Understanding, but the requirements that came out of it are.

File toolchain knowledge in the nearest `*AGENTS.md`, or in a rule if it is a decision. It is not
worthless; it is just not memory about the product.

**Outcomes are the exception, and they belong here.** The requirements a braindump distilled from a set of
meetings; the issues and PRs a piece of work produced and the state it left them in; what was specified but
not built, and who is carrying it. An `*AGENTS.md` documents what the code does, not what is still owed, so
this knowledge has no other home — and it is the first thing a next session needs. Record the artifacts and
their state, not a narrative of the work, and date it: a ticket number is a fact, a ticket's status is a
snapshot.

## Never export a rule as an Understanding

A preference, convention, or instruction from the user is a **rule**. Discovered behavior of the system
is an **Understanding**. The tell is the language: an Understanding written in must/never terms is a
rule wearing the wrong label, and it will be applied as evidence that can be overridden rather than as
a decision that cannot.

If knowledge needs must/never language, propose it as a rule under `.agents/rules/` instead
(see `manage-rule-system`).

## Promotion

- An Understanding that applies to nearly every task has outgrown the store — propose promoting it to
  a rule.
- An Understanding about a specific code area belongs in the nearest `*AGENTS.md`.

Propose the promotion; the user decides.

**Ask before promoting, and before a consume makes an incoming copy the current version of a slug this
workspace already holds; a write to a chosen destination does not ask.** Both change durable state
someone already chose to keep or rely on, so both ask first, every time. Merging into an existing
Understanding is no longer one of them — it is not an available operation: an improvement is written in
full as a new version under the same slug, which adds a copy and destroys nothing, so a local export
reports its outcomes rather than asking. Writing to a mode's default location, or to an explicit `--path`, needs no approval: the
destination was already chosen, and every write is reported. Exporting to the local disposable store
proposes the split first — via `AskUserQuestion`, recommending "write everything" — unless `--all` was
passed. `--all` is not only a waiver of that ask: it also widens what qualifies, so a marginal candidate
is written rather than dropped and the user prunes afterwards. An agent that never asks but filters hard
upstream has honoured the letter of the switch and defeated its purpose. The `ai-understanding` skill
owns the mechanics.

## Changelog

> AI loading note: Skip this section during routine task execution. Use it only when updating this rule file.

| Date | Change |
|:-----|:-------|
| 2026-09-19 | Initial version. |
| 2026-09-19 | Store path gained a subject tier: `<subject>/<slug>/`. |
| 2026-09-19 | `provenance.inherited` records which Understandings a session loaded and acted on. |
| 2026-09-19 | Outcomes (requirements distilled, issues/PRs produced and their state) named as a first-class kind of Understanding. |
| 2026-09-19 | Definition restated: input and outcome of a session's memory, for another agent to act on; qualifying test is "no other home". |
| 2026-09-19 | A unit is a question/answer pair; `trigger` renamed to `question`. |
| 2026-09-19 | Scope narrowed: functional/non-functional knowledge about the system only; toolchain knowledge is filed in `*AGENTS.md` instead. |
| 2026-09-19 | Subject folder gained a `-yyyyMMdd-HHmm` creation stamp; path example updated. |
| 2026-09-19 | Publish is an archive under `.context/`, not a tracked path; wording of the ask-before-writing carve-out updated. |
| 2026-09-19 | Vocabulary aligned to the export/import vs publish/consume split; `--all` named as the explicit waiver of the pre-write cut, resolving a rule/skill contradiction. |
| 2026-09-19 | Ask-before-writing carve-out narrowed to merge and promote; a named destination (default or `--path`) is now the approval for every write mode. |
| 2026-09-19 | LADR-010: a slug is a version key, not a unique name — an export run writes its own stamped folder, an improved unit is re-written in full, and the index shows the newest version of each slug. Importing gained the recency precedence rule (newer wins, analyse briefly, ask when unsure, the system outranks both). |
| 2026-09-20 | `--all` restated as breadth as well as prompt-suppression — it widens the qualifying bar, not only the ask. "Already holds" narrowed to the question rather than the topic: a record of a decision has no claim on the reusable reasoning behind it. |
| 2026-09-19 | Ask-before list corrected for LADR-010: merging is no longer an operation, so the carve-out is promote plus a consume that would make an incoming copy current. |
