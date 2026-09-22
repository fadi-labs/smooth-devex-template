---
name: ai-understanding
description: Export this session's hard-won knowledge into Understandings under .context/understandings/<subject>-<yyyyMMdd-HHmm>/<slug>.md (one file per unit, grouped into a subject folder stamped with when it was created), import matching ones back at task start, and publish/consume them across workspaces as a zip. Trigger on "export the understandings", "make an Understanding of this", "encode this", "what did we learn", "/ai-understanding", or when a session resolved something that cost real effort and would cost the same again. Not a session log and not code documentation.
allowed-tools:
  - Bash(python3 .agents/skills/ai-understanding/scripts/understanding_index.py:*)
  - Read
  - Write
  - Edit
  - Glob
  - Grep
models:
  claude: opus        # high-complexity; multi-turn judgment on what qualifies, merge/promotion decisions
  copilot: auto
  codex: gpt-5.5
---

# Understanding — Skill

An **Understanding** is the **input and outcome of a session's memory**, kept so another agent can act on
it: reusable, terse, structured, and holding what no code file or knowledge document already holds.

The last clause is the whole test, and the rest follows from the purpose — it is written for an agent to
act on, not for a human to read or an archive to keep:

- **terse**, because it competes for a context budget it does not control
- **structured**, because it must be matched before it is read
- **no narrative**, because an agent cannot act on a story
- **evidence, not orders**, because the agent must be able to override it when the system disagrees

Two kinds qualify. **Input** — what went into the work: requirements distilled from meetings, a braindump's
findings, a constraint someone stated once. **Outcome** — what came out: the issues and PRs a piece of work
produced and their state, what was decided, what was specified but left unbuilt, and anything learned in
passing that the work did not set out to learn.

The working store is **local and disposable** (`.context/` is gitignored). That is deliberate: memory accrues cheaply per workspace, and only what earns it gets published. Anything you want to survive this workspace must be published.

## TL;DR

1. Working store: `.context/understandings/<subject>-<yyyyMMdd-HHmm>/<slug>.md` — a stamped folder is **one export run**, holding only what that run produced.
2. `.context/understandings/INDEX.md` is a generated table of **unit + description + question**, one row per slug resolving to its newest version — the only file an agent reads to decide what to load, and the **first thing an export reads**.
3. One session may yield **several** Understandings; each is its own file, each stands alone, and they share a `provenance.session` value.
4. A slug is a version key, not a unique name. Same question → reuse the slug and write the complete improved unit into this run's folder. Different question → distinct slug. Never edit or delete a previous copy; newest wins.
5. Export writes the session's knowledge to disk; import reads it back. Publish/consume move it between workspaces as a zip archive.

## Store layout

```
.context/understandings/
  INDEX.md                            # generated — one row per slug, resolving to its newest version
  <subject>-<yyyyMMdd-HHmm>/          # ONE EXPORT RUN — holds only what that run produced
    <slug>.md                        # one Understanding (frontmatter + body)
    <slug>.assets/                   # only when a unit carries artifacts — repro, log excerpt, diagram
  _unfiled/                           # exempt from the stamp — a permanent catch-all, not a body of work
```

**A stamped folder is one export run; a slug is the knowledge.** The same slug appearing in several stamped folders is a **version chain**, not an error: the newest stamp is the current version, the rest are history. `INDEX.md` lists the current version only. The subject *name* is reused across runs so a body of work stays browsable together; the *stamp* is new every run. Use `_unfiled/` for an Understanding belonging to no particular topic.

Almost every unit is a single file — evidence normally belongs inline, quoted in the body, where a reader sees it without opening anything.

The `-yyyyMMdd-HHmm` stamp (24-hour, UTC — archives are consumed on other machines, so the zone is fixed) records when the run wrote the folder and is set once, never bumped — a unit's own `updated` field tracks freshness. It is what orders versions and what stops two sessions colliding on one folder name.

```
agent-memory-design-20260101-0900/store-decay.md     # v1 — superseded, on disk, unlisted
agent-memory-design-20260211-1430/store-decay.md     # v2 — superseded
agent-memory-design-20260305-1105/store-decay.md     # v3 — CURRENT, the only one INDEX.md shows
```

A unit that genuinely needs artifacts gets a sibling `<slug>.assets/` directory. Naming it after the slug is what prevents the collisions a shared directory would cause, and it is paid for only by the rare unit that needs it.

The subject is **not** how knowledge is found. Retrieval is by **question** — a future agent has a question in mind, not a subject, so the index lists every unit regardless of which subject produced it.

## Switches

Export and import are about **this session's memory**: export writes what the session learned to disk, import loads it back. Publish and consume are the separate, rarer cross-workspace operations.

| Switch | Effect |
|--------|--------|
| `--export [--path <dir>]` _(default)_ | **Reconcile against `INDEX.md`**, then write this run's new and improved units to a new `.context/understandings/<subject>-<yyyyMMdd-HHmm>/`, or under `--path` when given. Proposes the split first; writes nothing and creates no folder when nothing changed |
| `--export --all [--path <dir>]` | Same, but breadth-first: write every candidate without pausing for the user to cut the list, **and hold the qualifying bar loosely** — a marginal candidate is written, not dropped, because the user prunes afterwards |
| `--import` | Load Understandings whose question matches one the task will make you ask |
| `--publish [--portable-only] [--path <target>]` | Write every unit to a zip under `.context/understandings-publish/`, or to `--path` when given; `--portable-only` restricts the archive to `scope: portable` units |
| `--consume <zip> [--path <dir>]` | Unpack a published archive into the working store — `.context/understandings/` by default, or `--path` when given |
| `--promote <slug>` | Escalate an Understanding to a `*AGENTS.md` context file or a rule |
| `--index` | Regenerate `INDEX.md` from the store |
| `--review` | Advisory decay report — what is contested, never inherited, or overdue a re-check |

`--all` applies only to `--export`, where it means two things at once: **skip the cut**, and **widen
what qualifies**. The second half is the one that gets lost — an agent can honour "never ask" to the
letter while filtering hard upstream, and still report one unit as a complete export. Under `--all`,
resolve a marginal candidate toward writing it: the user asked for breadth and prunes what they did not
want. `--publish`'s scope filter is a separate switch, `--portable-only` — the two are unrelated despite
the old design overloading `--all` for both.

`--path` is always the **target** a mode writes to, overriding its default — never a source.
`--consume`'s source stays positional.

| Mode | Default target | `--path` overrides it to |
|---|---|---|
| `--export` | `.context/understandings/` | another store directory |
| `--publish` | `.context/understandings-publish/` | any file or directory path |
| `--consume <source>` | `.context/understandings/` | the store to unpack into |

Single-dash spellings of the long switches (`-all`, `-export`) are accepted as typed — they are
unambiguous here, and rejecting them would fail a run for a keystroke. An unrecognised switch is not
guessed at: say what was passed and ask.

## Export (default mode)

Exporting is the act of getting knowledge **out of the session and onto disk**, where it outlives the
conversation. Invoked bare, or with `--export`, this is what the skill does.

Read the whole session before writing anything. What qualifies is not "what we did" — it is what a
future agent would otherwise have to rediscover.

### Step one: reconcile with the store

**Read `.context/understandings/INDEX.md` before proposing or writing anything.** It lists every current
slug and question. This is the first action of an export, not a check performed later — stated only as a
prohibition further down, this rule has already been skipped once, and the store now holds the same two
questions answered three times each under six slugs.

Then classify every candidate against the index:

| Candidate matches | Action | Reported as |
|---|---|---|
| Nothing in the index, and the qualifying test below routes it **to** the store | Write it in this run's new folder | `new` |
| A current unit, same question, and this session changed nothing | **Write nothing** | `already known` |
| A current unit, same question, and this session refined it — corrected a claim, moved `confidence`, added a boundary | Write the **complete improved unit** into this run's new folder, reusing the slug | `improved` |
| A current slug, but a genuinely different question | New unit, disambiguated slug, in this run's folder | `new (disambiguated)` |
| Nothing in the index, but the qualifying test routes it **away** — another artefact already holds the **reusable** knowledge, not merely a decision about it | **Write nothing.** Name that file | `has another home` |

Rows two to four are decided against the index alone. Rows one and five **split the absent-index case
between them**, and *What qualifies: nothing with another home* below is what decides which of the two
applies — so no candidate ever maps to both, and an absent-index candidate is not `new` until that test
has been run on it. `has another home` is the exclusion's only reporting slot, and prose does not satisfy
it: **name the file that holds the knowledge**, or the skip is unauditable and indistinguishable from a
candidate you forgot. Under `--all` it should be rare — the bar is loose there, and a document that
covers part of the knowledge is not a claim on the rest.

**Judge "same question" generously.** This step decides everything, and judging it strictly is what
produced three answers to one question under three slugs. The test:

> If an existing unit's question would be **answered** by what you are about to write, it is the same
> question. The qualifier that makes yours feel new — *after the LADR-008/009 work*, *after the review
> sweep*, *for the stamped folders* — belongs in the **answer**, not in a new slug.

A narrower question is almost never a new question; it is the same question asked later. When genuinely
unsure, prefer `improved` over `new`: a wrongly-merged version is visible and fixable, a wrongly-split
slug silently defeats the whole model and nothing downstream reports it. A new slug is for knowledge that
answers a question **nothing in the index answers**.

**Slug reuse is what makes versioning engage.** A later session recording the same knowledge reuses the
slug so it becomes a version; a new slug declares new knowledge. Without that discipline two units cover
the same ground, both stay current, the index lists both, and the model never engages.

**Record what this step just told you.** Deciding `already known` or `improved` means you read the index
and the matching unit — so at that moment you know exactly what this session inherited. Put those slugs in
`provenance.inherited` on everything the run writes. Only what actually shaped the work counts; reading a
unit and setting it aside is not inheritance. If the run genuinely inherited nothing, omit the field and
**say so in the report** rather than inventing lineage. This is not bookkeeping — `--review` reads the
field back to find units nothing ever inherits, and a store where no unit carries it makes `--review`
report "nothing flagged" because it has nothing to read.

**Report every candidate under one of the five outcomes**, and give `has another home` the path it
requires. A silent skip is indistinguishable from a missed export.

### What a run writes

- **A run that produces something writes one new stamped folder** `<subject>-<yyyyMMdd-HHmm>/`, holding
  **only that run's output** — the `new` and `improved` units. It is not a snapshot of the store, and an
  unchanged unit is never copied into it.
- **A run that produces nothing writes nothing and creates no folder.** An export reporting only
  `already known` is a **correct outcome**, not a failure — say so, or agents pad the store to look
  productive. An empty stamped folder is reported as a problem by the generator.
- **Export is idempotent.** Export twice in one session and the second run writes nothing, leaving the
  store byte-identical. State that: it is the property that makes the reconcile step worth having.
- **An improved unit is written in full**, standing alone and readable without the version it replaces —
  never a diff, a patch, or an edit to the old file. It carries `provenance.supersedes: <previous-folder-name>`.
- **Previous copies are never edited and never deleted.** They are immutable history, exempt from
  validation, and unlisted in the index.

### What qualifies: nothing with another home

Work down this list. The store is the residue after the other homes have taken what is theirs.

| If it is… | It goes… |
|---|---|
| Visible in the code | nowhere — read the code |
| Functional intent about a code area | the nearest `*AGENTS.md` |
| A decision the user made | a rule |
| A design decision with trade-offs | an LADR in the nearest `*AGENTS.md` |
| A decision already recorded elsewhere, where the **reusable reasoning or diagnostic behind it is not** | **here** — that record has no claim on this |
| **Reusable, and none of the above has a claim on it** | **here** |

**A document that records *what was decided* has no claim on *how to recognise it, re-derive it, or
choose again*.** The ADR, NFR or LADR carries the verdict — the option selected, the number it moved.
The Understanding carries the failure signature that identified the problem, the miss profile of each
option not chosen, the diagnostic that separates this cause from the one it looks like. "We selected
`english`; recall 0.44 → 0.78" and "each configuration has a distinct miss profile, here is what each one
misses and how to choose" answer two different questions, and the first does not make the second
redundant. Ask what question the other document answers, not what it is about — a document **mentioning**
the topic is not a claim on it.

"Not written down yet" is not the same as "no other home". If something belongs in an `*AGENTS.md` and
nobody has written it, write it there — otherwise the store becomes the place for anything unfiled.

This is what excludes the toolchain. How a skill's script computes a diff, which Python version a scanner
needs, how a workflow's path filters combine — all true, all expensive to learn, all with a home beside the
tool they describe. The skill you used is never the subject: running a braindump is not an Understanding,
the requirements that came out of it are.

Outcomes are the one kind with no fallback. An `*AGENTS.md` records what the code does, not what is still
owed, so the state of a piece of work — its issues, its open decisions, its unbuilt specifications — lands
here or nowhere. Those units go stale fastest: give the date and the command that re-checks them.

### When to propose one unprompted

After resolving something about **the system** that cost real effort and would cost the same again: a non-obvious root cause in the domain, a constraint the data or an integration imposes, a convention not visible in the code, a rejected design and why it was rejected. Effort alone does not qualify it — a toolchain quirk can cost a whole afternoon and still belong in an `*AGENTS.md` rather than here.

**Propose it. Ask before writing.** The user decides what becomes memory.

### Splitting a session

A single session frequently contains more than one durable lesson. Split it — do not cram unrelated knowledge into one slug to keep the count down, and do not split one lesson into fragments that only make sense read together.

- One Understanding per **question**. If two pieces of knowledge answer different questions, they are two Understandings — and if one question needs two unrelated answers, it was really two questions.
- Each must stand alone. No "as established above", no reference to the conversation that produced it.
- Related slugs from the same session cross-link with `[[other-slug]]` and share one `provenance.session`.

When proposing a split, ask with `AskUserQuestion` — recommend **write every candidate** first, with
cutting specific slugs as the alternative, rather than a prose list a reader could mistake for output.
**With `--all`, skip the ask entirely and widen the bar** — write every candidate, resolving a marginal
one toward writing rather than dropping, and report what was written, so the user prunes afterwards
instead of beforehand. `--all` is a request for breadth: a one-unit export out of a session carrying
several lessons answers the letter of the switch and defeats its purpose.

### Writing one

Copy `assets/UNDERSTANDING.template.md` to `.context/understandings/<subject>-<yyyyMMdd-HHmm>/<slug>.md` — or under `--path` when given — and fill it.

Subject **name**: kebab-case, names the topic or piece of work. Reuse the name a body of work already
uses in the store — `ls .context/understandings/` shows them — so its runs stay browsable together.

Subject **folder**: always new, always this run. Create `<subject>-<yyyyMMdd-HHmm>/` with the current UTC
time, 24-hour (`date -u +%Y%m%d-%H%M`, e.g. `20260919-1432`), and write this run's output into it. Never
write into a folder an earlier run created. The one exception is a second export in the same minute with
the same subject: the name collides, so write into it — it is the same run for practical purposes, and the
stamp does not gain seconds to avoid this.

`_unfiled` is the home for a one-off that belongs to no topic, carries no stamp, and sorts oldest when it
holds a copy of a versioned slug. The subject is derived from the parent folder, so it is never written
into frontmatter and cannot drift.

Slug: kebab-case, names the **knowledge**, not the incident. `npgsql-enum-mapping-needs-datasource` — not `tuesday-db-bug`.

Frontmatter fields:

| Field | Meaning |
|-------|---------|
| `slug` | Must equal the file name without `.md`. Addresses the **knowledge**, not one copy of it — repeated across stamped folders it forms a version chain, and a `[[slug]]` resolves if any version exists |
| `description` | One line — what this knowledge is. Appears in `INDEX.md` |
| `question` | **Optional.** The question a reader has at the moment this applies, when there is a natural one — one question, one answer. Omit it on an outcome record, where `description` is the match. Appears in `INDEX.md` |
| `scope` | `portable` (true of the stack/tooling anywhere) or `repo-specific` (true only here). Governs export |
| `confidence` | `observed` (seen once), `verified` (reproduced, or confirmed against source), `contested` (the system disagreed). It records how the knowledge was obtained, **not that it is correct**. **One unverified claim sets the whole unit**: a unit is `verified` only if *every* claim in it was checked — infer one seam, one cause, one "probably" and it is `observed`, or verify that claim before writing. A single reasoned-but-unchecked line inside an otherwise-verified unit is how a wrong mechanism has twice propagated here, because readers trust the label, not the sentence |
| `links` | `[[slug]]` references to related Understandings |
| `agents_context` | Path to the nearest `*AGENTS.md` this bears on, when it concerns a specific code area |
| `provenance.learned` | Date, absolute |
| `provenance.session` | Shared by all slugs encoded from one session |
| `provenance.source` | What produced it — a failure, a doc, an experiment |
| `provenance.inherited` | `[[slug]]` list of the Understandings this session loaded **and acted on**. Omit when none |
| `provenance.supersedes` | The **previous folder name** (`agent-memory-design-20260919-1432`), not a path — enough to find the copy this one replaces, and it survives the file being moved. Set on an `improved` unit only; omit on a `new` one. Since the index shows only the newest, this is the only place a reader learns the unit is a third revision rather than a first |
| `updated` | Date of last change |

Body sections: **Answer** (direct operational guidance, answering the frontmatter question and nothing wider), **Why** (the reasoning or failure behind it — enough to judge an edge case the Answer does not cover), **Boundaries** (where it stops applying). The question lives in frontmatter only, so `INDEX.md` never drifts from the unit.

**Write it terse.** Every line earns its place or comes out. Cut what the reader already knows, what the code shows, and anything said once already. Prefer a table to a paragraph and a command to a description of a command. There is no length to fill and none to stay under — but a unit that does not fit on one screen is usually two units, or one unit padded. Density is the point: a reader who skips half of it has been failed twice, once by the noise and once by the signal they missed in it.

Keeping the answer inside the question's scope is what stops a unit over-reaching: an answer that outgrows its question means the question was too narrow, and a question no answer covers means it was too broad. Both are visible on one screen.

Record the lineage: list under `provenance.inherited` the Understandings this session imported and acted on. That is the store's only evidence of which knowledge is earning its place — a unit nothing ever inherits is either badly triggered or dead weight, and without the record you cannot tell those apart from knowledge that simply has not come up yet. It also gives the blast radius when a unit later turns out to be wrong.

A bracketed `[[slug]]` must resolve. When an ancestor is pruned or promoted away, drop the brackets rather than deleting the entry — the lineage is a historical fact and stays readable, without pinning the store to knowledge it no longer holds.

### Confidence moves

The field is worthless if it only ever gets set once.

| From | To | When |
|---|---|---|
| `observed` | `verified` | You used it and it held — confirming a unit you were relying on anyway is the cheapest verification there is, so take it |
| any | `contested` | The system disagreed. Record what you saw in the body; do not delete the unit |
| `contested` | `verified` | Someone re-checked and it holds — say what changed, in the changelog |

Raising confidence is a normal part of using the store, not a maintenance task. Lowering it is urgent: a
confidently wrong unit is the one failure mode worse than an empty store.

Note what it does **not** mean. `verified` says the claim was checked once, by someone, against something.
Two independent agents reading the source have found a false claim in a unit marked `verified`. Treat it as
provenance, not warranty — which is why the import protocol says verify rather than defer.

### Language

Understandings are **evidence, never orders**. Write them as "X behaves like Y; do Z" — an answer to the stated question, not an instruction issued in the abstract. Phrase the Answer deterministically — `If X, then Y; else Z` — never "should probably" or "might be worth".

If it needs must/never language, it is not an Understanding — propose it as a rule instead (see `.github/instructions/meta/understandings.instructions.md`). Never encode a user preference, convention, or instruction as an Understanding; those are rules.

### Slug reuse is versioning, not a collision

A slug already in the store is **not** a name clash to resolve — it is the address of knowledge you are
about to revise. The five outcomes are stated once, in *Step one: reconcile with the store* above; this
section only says what reuse means and what it is not.

- **Same question → reuse the slug**, and write the complete improved unit into this run's folder. That
  makes it the current version; the previous copy stays on disk as history.
- **Different question → a new slug**, disambiguated by what distinguishes it (`…-on-linux`,
  `…-under-aspire`) — never a numeric suffix, which describes a revision and the folder stamp already
  does that.
- **Editing, merging into, or deleting an existing copy is not an available outcome.** History is
  immutable. What was once a merge is now a new complete copy under the same slug.

Nothing mechanical catches a slug reused by accident — the generator can no longer tell a typo'd
collision from a deliberate revision, which is why the reconcile step runs first and why "same question"
is judged against the index rather than from memory.

After any write, regenerate the index:

```bash
python3 .agents/skills/ai-understanding/scripts/understanding_index.py
```

## Import (`--import`)

The reverse of export, and where the value is actually realised. This is also what the always-loaded rule
asks for at the start of a task, with or without the switch.

Read `INDEX.md` first and units second. Match on the **question** — or on `description` where a unit
carries none — against what the work at hand will make you ask.

**How many.** As many as genuinely match, which is usually none or one. Loading a unit costs context you
cannot spend twice, so a match has to be a match: the same question, not the same subject area. If three
match, read all three — but three matches on a store this size usually means the questions are too broad,
which is what `--review` is for.

**When nothing matches, say so.** One line, once. Silence is indistinguishable from not having looked, and
the next person cannot tell whether the store was consulted or ignored.

**When two Understandings conflict, the newer wins.** Decided by the folder stamp, falling back to
`updated`. This holds whether they are versions of one slug or two different slugs covering the same
ground. `INDEX.md` already resolves the version case for you — it lists the current copy only — so a
conflict you can see in the index is between two *slugs*.

**Analyse briefly, then proceed.** Note what changed between them if it is material, and carry on with the
newer. A conflict is not a blocker, and recency is the rule humans already use for new research.

**Ask when genuinely unsure** — when the older carries evidence or a boundary the newer dropped, or the two
disagree on something that changes what you are about to do and recency alone does not settle it. Say which
two units, what each claims, and recommend the newer. Do not silently pick.

**The system outranks every Understanding, however new.** Recency decides between Understandings, not
between an Understanding and reality. Say which unit, what it claims, and what you observed. Set its
`confidence: contested` — do not delete it, and do not quietly work around it. A unit that was true and
stopped being true is more informative than a missing one.

**Record what you used.** Any unit that changed what you did goes in `provenance.inherited` on whatever the
session exports later. Loading is not inheriting: only what shaped the work counts. This is the store's
only evidence of which units earn their place, and `--review` reads it back — a unit nothing ever inherits
is either badly asked or dead weight.

Rules always win a conflict with an Understanding. Flag the conflict rather than resolving it silently.

## Review (`--review`)

A store that only grows stops being readable. Nothing else notices, so this does:

```bash
python3 .agents/skills/ai-understanding/scripts/understanding_index.py --review
```

| Flag | What to do |
|---|---|
| `contested` | Confirm it against the system and raise it back to `verified`, or retire it |
| `never inherited` | The question probably does not match what anyone asks. Re-word it, or accept the unit was never needed and prune it. Counts inheritance of **any** version of the slug, so a unit revised three times is not reported unused because the lineage names an earlier copy |
| superseded copies | How many revisions of a slug sit on disk unlisted. Prune guidance only — nothing removes history automatically, and a deep chain is signal that the knowledge is still moving |
| overdue re-check | Read it against the current system. Outcome units are flagged after 30 days, knowledge after 90 |

Advisory only — it never changes the exit code, because none of it is wrong, it is just decaying. Act on it
when you are already in the store; do not make a project of it.

Pruning is a legitimate outcome. The store earns its retrieval cost or it does not.

## Publish (`--publish`)

Export puts knowledge on disk; publishing carries it **out of this workspace entirely**. `.context/` is
gitignored, so an archive that someone keeps is the only form that survives the workspace being destroyed.
The store is never shared through the repository (LADR-008).

- Destination: `.context/understandings-publish/understandings-<YYYYMMDD-HHMMSS>.zip` by default, or `--path` (a file or directory) when given. Outside the store, so the index generator never mistakes it for a subject folder, and never a tracked path.
- The archive mirrors the store: `<subject>-<yyyyMMdd-HHmm>/<slug>.md` with stamps carried verbatim — never re-stamped — plus each unit's `<slug>.assets/` and a regenerated `INDEX.md` covering only the published units.
- Publishing filters **per Understanding, not per subject** — a subject folder routinely mixes scopes. By default every unit publishes; pass `--portable-only` to restrict the archive to `scope: portable` units, for the cross-repo case. Never let `--portable-only` publish a `repo-specific` unit — that filter is the only thing preventing a local quirk from being shipped to another repo with provenance that makes it look universally verified.
- When `--portable-only` excludes a unit that a published unit links to, the archived copy drops the brackets around that `[[slug]]` and keeps the entry, so the archive's own index validates.
- Each archived copy records `provenance.published_from`; the working copy is left in place.
- No approval needed to write — the default destination or an explicit `--path` is the consent. Report what was published: the count, the destination, and the slugs, grouped by subject.

Sharing is sending someone the zip. Full contract: `references/publish-consume.md`.

## Consume (`--consume <zip> [--path <dir>]`)

The reverse of publish: another workspace's archive becomes available here.

The source is a local path to a published archive — always positional; `--path` overrides only the store it unpacks into (default `.context/understandings/`), never the source. How it arrived — mail, chat, a drive — is out of band; this skill does not fetch remote content. Extraction refuses any entry whose resolved path escapes the store (`..` segments, absolute paths, symlinks) and rejects the whole archive rather than unpacking part of it.

Reconciliation, per incoming slug. The key is the slug; an incoming copy keeps its own stamped folder, because a slug in two folders is a version chain rather than an error:

| Situation | Action |
|-----------|--------|
| Slug absent locally | Copy it in under its incoming stamped folder, set `provenance.consumed_from`, set `confidence: observed` |
| Slug present, same question | Copy it in under its incoming stamped folder as **another version** of that slug, with `provenance.consumed_from` and `confidence: observed`. The stamps decide which the index shows. **If the incoming stamp is newer than the local copy's, do not let it silently become current** — report the difference and ask; local belief is never replaced without the user seeing it |
| Slug present, different question | Bring it in under a disambiguated slug |

Consuming never silently changes what this workspace already believes. Incoming knowledge was verified somewhere else, against a setup that may differ, so it arrives as `observed` until something here confirms it. No approval needed to unpack — the source path is the consent. Report what was consumed: the count, the target store, and each slug's outcome (added, added-as-newer-version, added-as-older-version, or disambiguated).

## Promote (`--promote <slug>`)

An Understanding that keeps proving true has outgrown the disposable store:

- Concerns a specific code area → fold into the nearest `*AGENTS.md`, following `.github/instructions/meta/knowledge-conventional-contexts-quality.instructions.md`.
- Applies to nearly every task, or has become a decision rather than an observation → propose a rule under `.github/instructions/`, following `manage-rule-system`.

Propose the promotion; the user decides. Once promoted, the Understanding records where it went so the two do not drift into competing copies.

## Guardrails

- Writing to a mode's default location, or to an explicit `--path`, needs no approval — the location was already chosen, by default or by the user typing it. Report what was written and where, every time; removing the prompt must not remove the user's chance to notice.
- Ask before promoting, and before a `--consume` makes an incoming copy the current version of a slug this workspace already holds — both change durable state someone already chose to keep or rely on. A local `--export` writing an `improved` version does **not** ask: it adds a copy and destroys nothing, and the five outcomes are reported. On `--export`, propose the split with `AskUserQuestion` (recommending "write every candidate" first) before writing, unless `--all` was passed — the user's own instruction to skip that ask *and* to hold the qualifying bar loosely, writing a marginal candidate rather than dropping it.
- Never edit, overwrite or delete an existing copy of a slug. An improvement is a new complete copy in this run's folder; history is immutable.
- Never write an Understanding in must/never language.
- Never let an Understanding contradict a rule without flagging it.
- No secrets, tokens, or credential values in an Understanding — they are exportable by design. Record the shape of the problem, not the value.

## Changelog

| Date | Change | Ref |
|:-----|:-------|:----|
| 2026-09-19 | Initial version. | |
| 2026-09-19 | `--export`/`--import` are session↔disk; cross-repo moves became `--publish`/`--consume`. | |
| 2026-09-19 | Definition restated from its purpose — input and outcome of a session's memory, for another agent to act on — with a single "no other home" test replacing two separate qualifying rules. | |
| 2026-09-19 | Outcomes named as a first-class kind of Understanding: requirements distilled from meetings, and the issues/PRs/worktasks a piece of work produced and their state — none of which has an `*AGENTS.md` home. | |
| 2026-09-19 | A unit is now an explicit question/answer pair: frontmatter `trigger` became `question`, body `## Knowledge` became `## Answer`. | |
| 2026-09-19 | Scope narrowed to functional/non-functional knowledge about the system; knowledge about the agent toolchain is explicitly out and belongs in `*AGENTS.md` or setup docs. | |
| 2026-09-19 | Store gained a subject tier. Unit is `<subject>/<slug>.md`; artifacts, when any, go in `<slug>.assets/`. | |
| 2026-09-19 | `--publish` defaults to every unit; `--portable-only` replaces `--all` as the cross-repo scope filter (`--all` stays `--export`-only). | |
| 2026-09-19 | Subject folder gained a `-yyyyMMdd-HHmm` creation stamp (LADR-007). Reuse the existing stamped folder for work already in the store; mint a new one only for genuinely new work. `_unfiled` stays unstamped. | |
| 2026-09-19 | Publish is a zip under `.context/understandings-publish/`, consume takes a local zip (LADR-008); the tracked destination and the `ai-asset-sync` route are gone. Stamp is UTC. Export lists the store before choosing a folder; consume merges an already-present slug into its local folder. | |
| 2026-09-19 | `--path` added as the one target-override switch for `--export`/`--publish`/`--consume`, replacing ad-hoc destination language; a specified destination is now the approval, so Guardrails and the Publish/Consume sections no longer ask before writing to a default or `--path` location — only merge and promote still ask. `--export`'s pre-write cut is an `AskUserQuestion` (write-everything recommended first) rather than a prose list. Deterministic-phrasing line added to Language. | |
| 2026-09-20 | **LADR-011: `--all` means breadth, not only silence.** It waives the user's cut *and* loosens the qualifying bar, so a marginal candidate is written rather than dropped. The qualifying test separates a decision already recorded elsewhere from the reusable reasoning behind it, which that record has no claim on. The reconcile step gained a fifth outcome, `has another home`, reported with the path of the file that holds the knowledge. | |
| 2026-09-19 | **LADR-010: a slug is a version key, not a unique name.** An export run writes its own stamped folder holding only that run's output; an improved unit is re-written in full into it carrying `provenance.supersedes`; previous copies are immutable, unlisted and exempt from validation; `INDEX.md` shows the newest version of each slug. `duplicate_slugs` retired. Export gained the reconcile step (read `INDEX.md` first, four outcomes, generous same-question test, `provenance.inherited` from what it read); import gained the newer-wins precedence rule; consume treats an incoming duplicate as a version. | |
