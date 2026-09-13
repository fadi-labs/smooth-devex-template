---
name: create-hld
description: >
    Invoke to author a High-Level Design (HLD) at discovery / prototyping phase.
    Design-only: delivers intent + spec for AI and humans to build against — no
    implementation plan, no code outside examples/. Trigger keywords: "HLD",
    "high level design", "design doc", "architecture design", "create a design".
    Also triggers on /create-hld.
allowed-tools: >
    Bash(.agents/skills/create-hld/scripts/scaffold-hld.sh:*),
    Bash(.agents/skills/create-hld/scripts/hld-agents-rules.sh:*),
    Read, Write, Edit
models:
  claude: opus        # high-complexity; multi-step clarification gates + architectural judgment
  copilot: auto
  codex: gpt-5.5
---

# Create HLD — High-Level Design authoring

## TL;DR

Produce a `.docs/hlds/NNN-<slug>/` folder that captures **intent + spec** for a design at
discovery/prototyping phase. The HLD says *what* we are building, *why*, the decisions behind
it (LADRs), the quality bar it must meet (NFRs), and its architecture (diagrams). It does
**not** say *how to build it* — no implementation plan, no phasing, no code (except an optional
`examples/` folder). This skill is the source of truth for HLD structure in this repo.

Write it **terse, small, and only for needs that exist**. A short HLD a developer reads fully beats a
thorough one they skim. Leave the implementer room to be good at their job.

## Non-Negotiables

- **Design only.** No implementation plan, no execution phasing/sequencing, no sub-issue
  breakdown — that lives in the issue/work tracker. The HLD is for discovery/prototyping.
- **Requirement, not recipe.** State the outcome and its constraints. Name a mechanism *only* when
  choosing differently breaks a decision — otherwise it is the implementer's call. "Allocation must be
  race-safe; a lost race returns a `Result` failure" ✅. "Use a serializable transaction, or catch the
  unique violation and retry in a bounded loop" ❌.
- **YAGNI.** No decision, NFR, diagram, or extension point for a need that does not exist yet. Defer it
  in one line — an LADR `Open` item with a trigger — instead of designing it now.
- **KISS.** One decision per LADR, one quality attribute per NFR, one concern per diagram. If a section
  needs its own explanation to be followed, simplify the design rather than expanding the prose.
- **NFRs must be specific to this design.** Apply the specificity test below; delete any NFR that would
  read the same for any other feature in the repo.
- **Every NFR is measurable + verifiable.** Vague NFRs ("fast", "reliable") are forbidden.
- **No `Alternatives Considered` section.** Where a rejected option is one a competent person would
  actually try, fold it into the Decision as a single clause. Otherwise drop it.
- **No code** anywhere except `examples/`. README, LADRs, NFRs, and AGENTS.md are code-free.
- **AGENTS.md has no architecture section.** Architecture lives in `diagrams/`. The HLD
  AGENTS.md follows `scripts/hld-agents-rules.sh`, which deliberately omits System Context.
- **C1 is the floor, not the ceiling.** Always produce a C4Context. Investigate the design and
  *recommend* further diagrams (`references/diagram-selection.md`); do not pad by default.
- **Clarify before inventing.** Initiative name, goals, constraints, stakeholders, target
  system — ask, do not assume (Phase 1 of the AI workflow rules).
- **Every LADR and NFR is one file** — a horizontal concern spanning the vertical HLD.

## Economy — budgets and two tests

Budgets are ceilings, not targets. Over budget means cut content, not reformat it.

| File | Ceiling | Shape |
|---|---|---|
| LADR | ~400 words | Context ≤ 5 bullets · Decision ≤ 3 short paragraphs · Consequences ≤ 5 bullets |
| NFR | ~200 words | Requirement · Verification · Acceptance Criteria · Applies To |
| README | ~1500 words | ≤ 150 words per goal, before its acceptance criteria |
| AGENTS.md | ~700 words | Guardrails only, never narrative |

**NFR specificity test** — an NFR earns a file only if *"would this read the same for any other feature
in this repo?"* answers **no**. Delete it if yes **and** the concern is already bound by a documented
repo rule or ADR (typical examples: i18n coverage, keyboard operability, structured logging, HTTPS,
"write tests", "no secrets in code") — repeating a documented standard here dilutes the NFRs that
matter. If no repo rule covers it, keep it (or raise it as a repo-wide standard instead). An NFR
belongs here when *this* design puts an unusual demand on the attribute: a specific latency budget
under a named load, a migration that must not lose a specific field, a contract that must not break a
named consumer.

**Line test** — every line must prevent a wrong decision, state a measurable bar, or record a constraint
the reader cannot derive. Cut lines that justify the document ("this diagram earns its place"), restate
a neighbour, or narrate the authoring process.

## Invocation

`/create-hld <kebab-slug>` — or describe the design in natural language and follow the workflow.

## Output structure (the contract)

```
.docs/hlds/NNN-<kebab-slug>/
├── README.md            # human entry point: intent + spec (no impl, no code)
├── AGENTS.md            # AI-coder guardrails — NO architecture/System-Context section
├── diagrams/
│   └── c4-context.md    # C1 System Context (mandatory) + AI-recommended diagrams
├── ladrs/
│   └── LADR-NN-<slug>.md   # one decision per file
├── nfrs/
│   └── NFR-NN-<attribute>.md  # one quality attribute per file
└── examples/            # OPTIONAL — the only place code may appear
```

- `NNN` is 3-digit, zero-padded, next-available — the scaffold script computes it.
- `AGENTS.md` is plain-named (root of the HLD folder); the `load-agents-context` hook still
  auto-loads it. It is guardrails, not narrative.
- File shapes are defined by the templates in `assets/`; the scaffold script seeds them.

## Workflow

1. **Clarify scope** — initiative name, the problem and target outcome, key goals, hard
   constraints, stakeholders, the target system and its external dependencies. Do not invent.
2. **Scaffold** — run:
   ```bash
   .agents/skills/create-hld/scripts/scaffold-hld.sh <slug> [--title "Title"] [--examples]
   ```
   It prints JSON of the created paths. Add `--examples` only if code samples will help.
3. **Draft README.md** — Intent, Key Goals (each with **acceptance criteria / DoD**), Core
   Separation of Concerns (blockquoted thesis), Guiding Principle. Get the thesis and goals
   signed off before writing decisions. No rollout/phasing section, no risks section.
4. **Draft strategic LADRs** (`ladrs/LADR-01..N`) — one lightweight decision each, derived from the
   goals. Write only decisions the design actually forces: if the goals do not conflict on a point, it
   is not a decision, it is a detail — leave it to the implementer. Default status **Draft**.
5. **Investigate and recommend diagrams** — C1 is mandatory. Using
   `references/diagram-selection.md`, decide whether container / flow / sequence / ER / class
   diagrams add understanding. **Surface the recommendation to the user with a one-line
   rationale per diagram before writing them.** Then write into `diagrams/`.
6. **Draft NFRs** (`nfrs/NFR-01..M`) — one quality attribute per file: measurable Requirement,
   Verification mechanism, Acceptance Criteria, Applies-To. Run the specificity test on each before
   writing it; expect to end with **two to four** NFRs, not a full attribute checklist. Reference them
   from the README NFR table.
7. **Draft tactical LADRs** only if a *how* decision is genuinely constrained (runtime, protocol,
   config). Number after the strategic ones; never renumber.
8. **Draft AGENTS.md** — apply `scripts/hld-agents-rules.sh`. Derive Non-Negotiables from the
   LADRs, fill the decisions and NFR pointer tables. No architecture section.
9. **Wire the tables** — README LADR table and NFR table list every file with status.
10. **Cut pass** — re-read every file against the budgets and the two tests. Remove justification,
    restatement, and prescribed mechanism. Expect to delete, not to polish.

To read the AGENTS.md rules at any point (agent-agnostic, no hook needed):
```bash
.agents/skills/create-hld/scripts/hld-agents-rules.sh
```

## Quality bar before marking ready

- [ ] Every Key Goal has acceptance criteria / DoD.
- [ ] Every LADR has Context, Decision, Consequences — and is within budget.
- [ ] Every NFR has a measurable target AND a verification mechanism AND acceptance criteria.
- [ ] Every NFR passes the specificity test — no project-standard restatements.
- [ ] No prescribed mechanism that a decision does not force; the implementer still has choices.
- [ ] Nothing designed for a need that does not exist yet; deferrals are one-line `Open` items with triggers.
- [ ] No `Alternatives Considered` sections.
- [ ] C1 diagram present; every extra diagram is one-concern and answers something C1 cannot.
- [ ] AGENTS.md has no architecture section, no code, no impl/phasing.
- [ ] No code outside `examples/`.
- [ ] Mermaid renders (no syntax errors).
- [ ] All cross-links are relative and resolve. No `[TODO]`; use `TBD` with owner/trigger.

## Agent-agnostic notes

- Scripts are `bash` + coreutils only; no Claude-specific behaviour.
- The AGENTS.md quality rules ship inside the skill (`scripts/hld-agents-rules.sh` + the
  summary above), so Codex / Copilot / Cursor — which do not run Claude Code hooks — are fully
  self-contained. The repo's global `knowledge-rule-enforce.sh` hook is unaffected and still
  governs general (non-HLD) AGENTS.md files.

## References

- `references/status-vocabulary.md` — Draft / Prototype / Accepted lifecycle; strategic vs tactical.
- `references/diagram-selection.md` — when to add each diagram type beyond C1.

## Changelog

| Date | Change | Ref |
| :---- | :---- | :---- |
| 2026-06-16 | Created — design-only HLD skill, made project-agnostic for the smooth-devex template. | — |
| 2026-09-13 | Ported the economy bar from downstream: terse/YAGNI/KISS non-negotiables, requirement-not-recipe rule, per-file word budgets, NFR specificity test, line test, closing cut pass, and removal of `Alternatives Considered` from the LADR template. | — |
