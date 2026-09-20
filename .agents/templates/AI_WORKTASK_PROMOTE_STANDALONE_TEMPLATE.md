# Task: [one-liner task description]

## Execution Profile
- **Recommended session model:** [model]   <!-- human action: set with /model BEFORE starting; switch at a gate if a later phase needs more reasoning -->
- **Path:** Lightweight (0→1→6→7→8) | Full (0→1→2→3→4→5→6→7→8)
- **Subagents:** none | Explore (read-only fan-out) | worktree-isolated writers
- **Commits during execution:** not allowed | allowed via the git-commit skill
- **Push:** never

## Contexts
- [ ] list relevant context documents, domain files, or knowledge sources
- [ ] if no context document exists for this feature, add one here and include "create context document" in Instructions

## Instructions
- [ ] list specific requirements and acceptance criteria

## Constraints

### Context Loading (Phase 0 — MANDATORY FIRST)
- **Load domain/feature context BEFORE asking clarifying questions** — you cannot ask intelligent questions without understanding existing patterns
- Use the `context-load-context` skill with `[domain]` to find/create functional context, or rely on the `load-agents-context` PostToolUse hook which auto-injects ancestor `*AGENTS.md` on first Read/Edit

### Git Behavior

`git-policy.instructions.md` is authoritative. Nothing in this template overrides it.

- **Commits** are governed by the **Commits during execution** field in the Execution Profile above. Default: **not allowed** — report the change set and stop; the user commits.
- When the field allows commits, make them by **invoking the `git-commit` skill**, never by composing a message inline — the skill runs conventional-format validation and logical-unit grouping.
- **Push: never.** Manual review is required before any push.

### Phase Output Rules (MANDATORY — no exceptions)

1. **Label every phase** — Output `## Phase N: Name` as a visible header before executing each phase
2. **Label every skip** — If skipping a phase, output: `## Phase N: Name — Skipped: [one-line reason]`
3. **Sequential execution** — Phases MUST execute in declared order. Never reorder, combine, or nest (e.g., doing Phase 5 work inside Phase 6 is a violation)
4. **No silent phases** — Every phase in your chosen path MUST appear in output. If the user can't see it, it didn't happen

> **FALLBACK copy.** `ai-workflow-rules.instructions.md` is authoritative. This copy exists for runners that do not auto-load `.agents/rules/` (e.g. Codex) and MUST be kept in sync with the rule on every workflow change.

### Execution Phases

Follow in order. **Do not skip phases without outputting the skip reason. Do not proceed without explicit user confirmation at gates.**

| Phase | Name | Gate? | Purpose | Who |
|-------|------|-------|---------|-----|
| 0 | Context Load | 🛑 MANDATORY | Read documents from **Contexts** section above | session |
| 1 | Odin (Clarify) | 🛑 GATE | Consolidate domain/technical/test clarifications | session (PO → Architect → QA lenses, in sequence) |
| 2 | Thoth (Analyze) | | Analyze tech stack, determine tech requirements, identify patterns | session (read-only fan-out allowed) |
| 3 | Forseti (Specify) | | Create technical specification with architectural decisions | session |
| 4 | Tyr (Plan) | 🛑 GATE | Present implementation plan + module breakdown | session (per-stack lenses, in sequence) |
| 5 | Frigg (Document) | | Update AGENTS.md with approved plan under `## Requirements` | session |
| 6 | Thor (Execute) | | 🔨 YOLO MODE — implement on the working branch | session (parallel writers only when worktree-isolated) |
| 7 | Heimdall (Review) | | Quality gate — review skill + spec/implementation sync check | session + review skill |
| 8 | Bragi (Record) | 🛑 MANDATORY | Document actual implementation; stop before committing unless the profile allows commits | session |

**Lightweight path** (trivial tasks): Phase 0 → 1 → 6 → 7 → 8
Use when: single file, no architectural decisions, clear requirements.

**Full path** (non-trivial tasks): Phase 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8
Use when: 3+ files, new patterns, cross-cutting concerns, or ambiguous scope.

### Subagents

**Default: none.** Every subagent starts cold, re-derives context this session already holds, and returns only text. Spawn one only in these three shapes:

1. **Read-only fan-out** (Phase 2) — a broad sweep across many files or naming conventions where only the conclusion is needed, not the file dumps. `Explore` in Claude Code; the runner's read-only search agent elsewhere.
2. **Worktree-isolated parallel writers** (Phase 6) — each writer in its own git worktree, with an explicit merge step owned by the session. Without worktree isolation and a merge step, implement sequentially.
3. **Independent review** (Phase 7) — the runner's existing review skill, not ad-hoc reviewer agents.

**Parallelism means batching tool calls, not spawning agents.** Issue N independent reads, greps, or builds of unrelated projects in a single message. Sequence only when one call's output feeds the next. Never run two write operations against the same file, and never run concurrent `dotnet build` / `dotnet test` over the same solution.

Where a phase does spawn a subagent, carry the model hint in the repo's per-runner form (as in `git-commit/SKILL.md` and `git-commit-push/SKILL.md`) — `claude:` / `copilot:` / `codex:`. The *session* model is not set by this file; it is a human action (`/model`), recorded in the Execution Profile.

---

## Phase 1: Odin (Clarify)

**No subagents.** One session applies three lenses in sequence over the context loaded in Phase 0, then consolidates them into a single question list. The deliverable is that list — three cold agents plus a merge produces less, later.

### PO lens
- Business intent and value proposition
- Acceptance criteria and success metrics
- User stories and edge cases
- Scope boundaries (what's IN, what's OUT)
- Related business context or dependencies

### Architect lens
- Technical feasibility and constraints
- System integration points and dependencies
- Performance, scalability, or security implications
- Trade-offs between proposed approaches
- Impact on existing architecture

### QA lens
- Testing scope and coverage expectations
- Acceptance criteria validation (are they testable?)
- Test tiers required: L0 (unit), L1 (component), L2 (integration)
- Known edge cases or failure scenarios to cover
- Regression test impact

### Consolidation & Gate

```markdown
## Phase 1: Odin (Clarify) — Consolidated Findings

### Business Clarifications
- [finding and question/recommendation]

### Technical Clarifications
- [finding and question/recommendation]

### Test Scope Clarifications
- [finding and question/recommendation]

### Assumptions validated
- [what was already clear, no question needed]

---

**Gate Question:**
Does this consolidated understanding capture your intent?
Reply 'approved' to proceed to Phase 2, or provide corrections.
```

**If requirements are already clear from the task description, state your understanding and proceed without waiting. Otherwise, wait for the user's response before proceeding.**

---

## Phase 2: Thoth (Analyze)

**Prerequisite:** Phase 1 clarifications resolved.

**Responsibilities:**

1. **Determine technology stack requirements** — this output selects the per-stack work in Phase 4:
   - Backend required? (Database changes, API endpoints, server-side logic, service integrations, message queues)
   - Frontend required? (User-facing UI changes, in whatever frontend stack this repo uses)
   - Infrastructure/DevOps required? (Deployment, configuration, CI/CD, security)
   - **Output**: Clear YES/NO for each, with justification

2. **Analyze existing patterns and conventions**:
   - Similar features already implemented — what patterns do they follow?
   - Existing architecture decisions (ADRs) that apply to this task
   - Code organization, naming conventions, testing patterns
   - Technology stack baseline (what's already in use)

3. **Identify architectural constraints and dependencies**:
   - How does this task integrate with existing systems?
   - Breaking changes or migration paths needed?
   - Performance or scalability constraints
   - Security/compliance considerations

**Optional read-only fan-out.** This is the one phase where a subagent is routinely justified: if locating the relevant patterns means sweeping many directories or naming conventions, dispatch a read-only search agent and take its conclusion. Model hint at that spawn point:

```yaml
models:
  claude: sonnet
  copilot: gpt-5.4
  codex: gpt-5.4
```

**Output format:**

```markdown
## Phase 2: Thoth (Analyze)

### Technology Stack Requirements
- **Backend**: YES — [justification: DB changes, API endpoints, etc.]
- **Frontend**: NO — [justification: no UI changes]
- **Infrastructure**: NO — [justification: no deployment changes]

### Existing Patterns & Conventions
- Similar features: [list and reference]
- Relevant ADRs: [which decisions from code-review-standards.instructions.md apply]
- Code organization: [where should new code go]
- Testing patterns: [what test structure to follow]

### Architectural Constraints
- Integration points: [where this connects]
- Performance considerations: [if any]
- Security implications: [if any]
- Migration/breaking changes: [if any]

**Ready for Phase 3.**
```

**Exit check**: proceed to Phase 3 only if tech stack requirements are clear. (Self-check, not a user stop.)

---

## Phase 3: Forseti (Specify)

**Prerequisite:** Phase 2 analysis complete (tech stack determined).

**Responsibilities:**

1. **Create technical specification** with architectural decisions:
   - Architecture diagram or data model changes (if applicable)
   - API contracts, database schema changes (if backend)
   - UI/component structure (if frontend)
   - Error handling and logging strategy (following backend-logging-conventions.instructions.md)

2. **Document architectural decisions** — Use LADR format:
   - Decision title
   - Context (why this decision is needed)
   - Decision (what was chosen)
   - Consequences (what changes as a result)
   - Reference to code-review-standards.instructions.md ADRs if applicable

3. **Define testing approach**:
   - Test tiers and coverage expectations
   - Edge cases and failure scenarios
   - Integration test requirements (if applicable)

4. **Specify constraints and non-functional requirements**:
   - Performance targets
   - Security requirements
   - Scalability considerations
   - Compliance/audit trail needs

**Output format:**

```markdown
## Phase 3: Forseti (Specify)

### Technical Specification

[Include architecture diagrams, data model, API contracts, etc.]

### Architectural Decisions

**LADR-XXX: [Decision Title]**
- Context: [why this decision]
- Decision: [what was chosen]
- Consequences: [what changes]
- Related ADRs: [links to code-review-standards.instructions.md decisions]

[Additional LADRs if needed]

### Testing Approach
- Test tiers: [L0 (unit) / L1 (component) / L2 (integration) requirements]
- Coverage targets: [e.g., >80% for critical paths]
- Edge cases: [high-risk scenarios identified in Odin]

### Non-Functional Requirements
- Performance: [targets or constraints]
- Security: [requirements from clarifications]
- Scalability: [expectations for growth]

**Ready for Phase 4.**
```

**Exit check**: proceed to Phase 4 only if the specification is complete and aligns with Phase 1 clarifications. (Self-check, not a user stop.)

---

## Phase 4: Tyr (Plan) — 🛑 GATE

**Prerequisite:** Phase 3 specification complete.

**Sequence (one session, no subagents):**

1. **Create the overall implementation plan**:
   - Ordered list of implementation steps
   - Module/component breakdown
   - File-level changes and dependencies
   - Risk mitigation strategies
   - Estimated scope (files touched, effort)

2. **Apply a per-stack engineer lens for each stack answered YES in Phase 2**, in sequence — same session, same context:
   - Input: Phase 3 spec + overall plan
   - Output: a stack-specific plan — units to add or change, data/contract changes, tests, dependencies

3. **Reconcile the per-stack plans**:
   - Check integration points and conflicts between stacks
   - Adjudicate conflicts before presenting
   - Present the consolidated plan to the user

**Output format:**

```markdown
## Phase 4: Tyr (Plan)

### Overall Implementation Strategy
- Step 1: [implementation step] (File: X)
- Step 2: [implementation step] (File: Y)
- Dependencies: [what must complete before what]
- Risks: [identified risks and mitigation]

### Per-Stack Plans (one block per stack answered YES in Phase 2)

**[Stack]**
- Modules/units: [new or modified]
- Data & contract changes: [schema, API, message shapes, persisted state]
- Tests: [tier and location for each new behavior]
- Dependencies: [what this stack depends on, and what depends on it]

### Integration Points
- [How the stacks interact]
- [Conflict resolution if any]

**Gate Question:**
Does this plan look correct? Reply 'approved' to proceed, or provide feedback.
```

**Gate**: wait for user approval before proceeding to Phase 5.

---

## Phase 5: Frigg (Document)

**Prerequisite:** Phase 4 plan approved by user.

**Responsibilities:**

1. **Update domain AGENTS.md** (or create if missing):
   - Add to `## Requirements` section: accepted plan from Phase 4
   - Document architectural decisions (from Phase 3 LADRs)
   - Record tech stack requirements and integration points
   - Add test references (L0/L1 tier, test sub-folder paths)

2. **Update or create project ADRs** (`.docs/adrs/`):
   - For each Phase 3 LADR: create corresponding ADR file if it's a foundational architectural decision
   - Update existing ADRs if implementation changes behavior they document

3. **Update root AGENTS.md** if needed:
   - Cross-reference new feature/domain context document
   - Note significant architectural changes

4. **Update changelog** in context documents:
   - Record what was changed and why (for future reference)

**Output format:**

```markdown
## Phase 5: Frigg (Document)

### Context Documentation Updated
- [Domain]_AGENTS.md: [sections updated]
- Root AGENTS.md: [sections updated]

### Architectural Decisions Recorded
- LADR-XXX: [ADR file created or updated]
- LADR-YYY: [ADR file created or updated]

### Changelog Entries
- [Date] | [Change] | [Reference to this task]

**Ready for Phase 6.**
```

---

## Phase 6: Thor (Execute)

**Prerequisite:** Phase 5 documentation complete (or skipped with a reason).

**Sequential by default.** One writer works through the Phase 4 plan in order. Implement completely — no TODOs, no stubs. Batch independent *reads* freely; keep *writes* sequential. On failure, fix forward; if blocked after 2 attempts, report status with options and wait for user guidance.

**Parallel writers are allowed only with worktree isolation plus an explicit merge step:**

- Each writer gets its own git worktree. **Never two writes to the same file**, within a worktree or across worktrees.
- **Never run concurrent `dotnet build` / `dotnet test` over the same solution.** Build and test once, in the session, after the merge.
- The session owns the merge step and the post-merge build + test run.
- **Weigh the cost first:** a .NET worktree pays a fresh `dotnet restore` per agent, and EF Core migration ordering still collides at merge — for most tasks sequential is faster end to end.
- Model hint at that spawn point:

```yaml
models:
  claude: sonnet
  copilot: gpt-5.4
  codex: gpt-5.4
```

**Output format:**

```markdown
## Phase 6: Thor (Execute)

### Implementation Complete
- [File 1]: [what was implemented]
- [File 2]: [what was implemented]
- Tests: [all passing, coverage X%]

**Ready for Phase 7 (Review).**
```

**No user gate** — and no commits either, unless the Execution Profile allows them.

---

## Phase 7: Heimdall (Review)

**Prerequisite:** Phase 6 execution complete.

**Invoke the runner's existing review skill on the diff** rather than spawning ad-hoc reviewer agents — `/code-review` in Claude Code, the equivalent review skill elsewhere. It already covers code quality, pattern consistency, security and test adequacy, and it reviews what was actually written.

Then apply the two checks a diff review does not cover:

1. **Specification sync** — does the implementation match the Phase 3 spec (or the task Instructions, if Phase 3 was skipped)? Are the LADR decisions honored? Any design issue introduced during execution?
2. **Acceptance criteria** — is every criterion from Phase 1 demonstrably met, with tests at the right tier (L0 unit / L1 component / L2 integration)?

**Consolidation & Decision:**

- If all pass: proceed to Phase 8
- If issues found: present to user with options:
  - **Option A**: Fix issues in a follow-up execution (re-run Phase 6 with feedback)
  - **Option B**: Accept known issues and document (update AGENTS.md)
  - **Option C**: Block and ask for clarification/requirements change

**Output format:**

```markdown
## Phase 7: Heimdall (Review)

### Review Skill Findings
- [finding + remediation, or "none"]

### Specification Sync
- ✅ Implementation matches Phase 3 spec
- ✅ Architectural decisions honored
- Issues (if any): [list with remediation]

### Acceptance Criteria & Test Coverage
- Acceptance criteria: ✅ covered
- Edge cases: ✅ covered
- Test tiers: [L0/L1/L2 added or updated]
- Coverage %: [X%]

### Gate Decision
- ✅ Ready for Phase 8 (record)
- OR ⚠️ Issues found — [ask user for remediation approach]
```

---

## Phase 8: Bragi (Record) — 🛑 MANDATORY

**Prerequisite:** Phase 7 passed (or user approved known issues).

**Mandatory to perform — and it stops before committing.** Recording is never skipped; committing happens only if the Execution Profile allows it.

1. **Update AGENTS.md context document**:
   - Record actual implementation details (not just planned)
   - Update Tech Stack section with what was actually used
   - Update Key Behaviors if implementation differs from spec
   - Add Changelog entry: date, change, reference

2. **Update or create ADRs**:
   - If Phase 3 LADRs are still accurate: mark as finalized
   - If implementation changed decisions: update ADR with actual outcome
   - Add implementation status and rationale

3. **Finalize changelog**:
   - Comprehensive entry describing what was implemented
   - Breaking changes (if any)
   - Migration instructions (if needed)
   - Reference to this task

4. **Commits — per the Execution Profile's Commits field:**
   - **Not allowed (default):** report the change set — files touched, what changed, and a suggested commit grouping — then **stop**. The user commits.
   - **Allowed:** commit by **invoking the `git-commit` skill** so conventional-format validation and logical-unit grouping run. Never compose commit messages inline. One logical unit per commit; include the worktask/ticket reference.
   - **Push: never.**

**Output format:**

```markdown
## Phase 8: Bragi (Record)

### Documentation Updated
- [Domain]_AGENTS.md: [sections changed]
- ADR files: [updated with actual implementation details]
- Root AGENTS.md: [if applicable]

### Changelog Entry
[Comprehensive entry for release notes]

### Change Set
- [File]: [what changed]
- Suggested commit grouping: [logical units]

### Commits
- Commits not allowed by this worktask — change set reported above, awaiting the user
- OR: [conventional message per commit, created via the git-commit skill]

### Task Complete ✅
[Change set ready for review | Commits created on [branch]; push not performed.]
```

---

## Changelog

> AI loading note: Skip this section during routine task execution. Use it only when updating this template.

| Date | Task | Changes |
|------|------|---------|
| 2026-05-30 | | Initial version. |
| 2026-09-20 | Worktask template & hook remediation | Removed the git-policy override and the autonomous-commit instructions — commits are now a per-task Execution Profile field routed through the `git-commit` skill, push never. Added `## Execution Profile`, replacing the 17-row phase/model table and the fabricated cost/quality metric; model hints now bind only at spawn points, in the per-runner `claude:`/`copilot:`/`codex:` form. `Agent Fleet Autonomy` → `Subagents` (default none, three justified shapes; parallelism means batched tool calls). Phases 1/4/7 no longer spawn specialist rosters; Phase 6 is sequential unless worktree-isolated with a merge step; Phase 7 delegates to the runner's review skill. Genericized the frontend/stack specifics. `load-context` → `context-load-context`; test tiers corrected to L0 unit / L1 component / L2 integration. Self-check "Gate"s renamed to "Exit check". Added the FALLBACK banner naming `ai-workflow-rules.instructions.md` authoritative, plus this `## Changelog` heading. |
