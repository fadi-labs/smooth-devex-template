# AGENTS.md

This file provides guidance for AI coding agents working in the Project repository.

> **⚠️ TEMPLATE NOTICE — read before working.**
> This repository is currently a **template**. `Project` is a placeholder name used throughout the `.agents` tree, root `AGENTS.md`, rule files, skill docs, and the solution/project layout (`Project.slnx`, `src/Project.*`, `tests/Project.*`).
>
> **As soon as the project is given a real name, you MUST:**
> 1. Replace every occurrence of `Project` / `project` (PascalCase namespaces/paths and lowercase prose) across all `.agents` files, root `AGENTS.md`, rule files, skill docs, `Project.slnx`, and the GitHub URL/slug with the chosen name.
> 2. Update the glossary and the Project Overview description below to describe the real project.
> 3. **Remove this entire TEMPLATE NOTICE block** — including this instruction — once the rename is complete.

## Project Overview

Project is an AI-spec-driven, AI-agnostic development project. It documents reusable patterns, blueprints, and component specifications that guide automated and AI-assisted software delivery. _(Placeholder description — update once the project is named; see Template Notice above.)_

**Tech stack:** .NET 10 · ASP.NET Core · Clean Architecture (Domain / Application / Infrastructure / Host) · EF Core + PostgreSQL · Mediator (source-gen CQRS) · xunit.v3

## AI Context Files

`AGENTS.md` and `*AGENTS.md` are **AI-coder contextual knowledge documents**. Read them like `CLAUDE.md` (or your agent's equivalent standard context file): they are first-class, authoritative context — not optional reference material. Before changing code, treat any `AGENTS.md` / `*AGENTS.md` in scope as required reading.

These documents capture the **functional requirements and intent behind the code** — the "why", constraints, boundaries, and non-obvious behaviors that source code alone does not communicate. Use them to understand what the code is supposed to do before you change how it does it.

Contextual knowledge is layered, and applies at **multiple levels** — read every level that governs the code you touch (specific overrides general):

- **Domain** — the broad business/functional area.
- **Sub-domain** — a bounded slice within a domain.
- **Feature** — a specific capability or vertical slice.
- **Technology** — cross-cutting technical concerns (persistence, messaging, logging, etc.).

This root `AGENTS.md` is the top-level document; nested `*AGENTS.md` files inherit from it and add local context closest to the code. When working in a folder, the nearest `*AGENTS.md` is the most authoritative for that code.

Keep `*AGENTS.md` files synchronised with code and documentation changes. Functional `*AGENTS.md` files in feature folders are auto-loaded by the `load-agents-context` PostToolUse hook on the first Read/Edit in their directory tree — no manual registration required.

### Required Maintenance

- Every PR should create or update at least one `*AGENTS.md` file.
- Update the closest context file to the code you change. Prefer local context over adding more content to this root file.
- When domain model or structural shape changes, also update the relevant implementation or architecture context.

### Placement Rules

- Functional feature context belongs close to the feature code.
- Cross-cutting concerns belong under `.docs/hlds/02-nfrs/` or the nearest `*AGENTS.md`.
- Avoid creating duplicate context files that restate the same plan at multiple levels without adding new information.

## Understandings

Alongside rules (decisions) and `*AGENTS.md` (functional intent) there is a third kind of knowledge: **Understandings** — discovered knowledge about how the system actually behaves, stored under `.context/understandings/<subject>-<yyyyMMdd-HHmm>/<slug>.md` (gitignored, per-workspace — a subject folder, stamped in UTC with when it was created, groups a session's lessons, one file per Understanding inside it). Each is a **question and its answer**. They are evidence, not orders: apply one when its question matches one you are asking, flag it when the code contradicts it, and let the rule win any conflict. Read `.context/understandings/INDEX.md` at task start to find the ones whose question applies. The store is never shared through the repository: knowledge survives a workspace only as a published zip that someone keeps. Governance: `.agents/rules/meta/understandings.instructions.md`; mechanics: the `ai-understanding` skill.

## Implementation Docs

All planned work is tracked as worktasks under `.context/work-tasks/` (gitignored — local only). Use the `create-worktask` skill (`/create-worktask <kebab-slug>`) to scaffold and populate a new one.

## Repository Layout (Navigation)

| Layer | Path | Purpose |
|---|---|---|
| Domain | `src/Project.Domain/` | Core entities, value objects — no external deps |
| Application | `src/Project.Application/` | Vertical-slice use cases via Mediator — `Features/<Name>/`, shared code in `Common/` |
| Infrastructure | `src/Project.Infrastructure/` | EF Core + PostgreSQL (`Persistence/`), HTTP clients (`Clients/`) |
| Host | `src/Project.Host/` | ASP.NET Core Web API, Serilog, Scalar OpenAPI |
| ChatHost | `src/Project.ChatHost/` | Standalone LLM microservice — owns Anthropic SDK; talks to Host via HTTP only |

Detailed backend coding rules are maintained in `.agents/rules/backend/` and scoped per-file via frontmatter (see Rules section).

## Rules

All rules live under `.agents/rules/` as `*.instructions.md` files and are auto-loaded every session by Claude Code, Cursor, Copilot, and Codex via the symlinks/path-references documented in `.agents/AI_DEVELOPMENT_AGENTS.md`. Applicability is scoped **per-file** via frontmatter (`paths` for Claude, `globs`+`alwaysApply` for Cursor, `applyTo` for Copilot) — e.g. backend rules carry `**/*.cs` so they attach when a C# file is opened. Rules are organized into category subfolders for navigation; the folder is organizational only and does not change loading. One exception to "auto-loaded every session": prompt-scoped rules may be **deferred for Claude** and re-injected on demand by a `UserPromptSubmit` hook (e.g. `code-review-standards` loads only on review prompts via `.agents/hooks/code-review-standards-context.sh`; Cursor/Copilot still load it always). See `.agents/rules/meta/rules.instructions.md` ("Hook-deferred rules") for the file convention and `.agents/skills/manage-rule-system/SKILL.md` for the directory contract.

### Rule Categories

| Category | Folder | Contents |
|----------|--------|----------|
| _(cross-cutting)_ | `.agents/rules/` (flat) | `ai-workflow-rules`, `code-review-standards` (Claude: hook-deferred to review prompts), `project-overview`, `clean-code`, `solid-principles` |
| git | `.agents/rules/git/` | `git-policy`, `pr-standards` |
| meta | `.agents/rules/meta/` | `rules` (file convention), `knowledge-conventional-contexts-quality` (AGENTS.md quality), `understandings` (rules vs discovered knowledge) |
| skills (`.agents/skills/**`) | `.agents/rules/skills/` | `skill-secret-handling` (secrets via runtime env only); `skillspector-pre-pr` (run/predict the static SkillSpector scan and ship baseline updates in the same PR) |
| backend (`**/*.cs`) | `.agents/rules/backend/` | `api-mediator-validation` (Minimal API + Mediator + FluentValidation fail-fast); `architecture-slices` (clean-architecture boundaries, vertical-slice Features); `backend-logging-conventions` (Information vs Debug levels); `external-api-clients` (Refit list vs singular client split, HybridCache adapter); `migrations` (`[ExcludeFromCodeCoverage]` requirement); `readonly-collections` (`AsNoTracking` → `T[]`; `List<T>` only when mutated); `wiremock-stubbing` (TestFramework.Aspire single-source stub helper) |

## Build / Test Commands

```bash
dotnet build Project.slnx                     # build
dotnet test  Project.slnx                     # run all tests
dotnet run --project src/Project.AppHost      # dev Aspire AppHost
dotnet run --project src/Project.ChatHost     # ChatHost standalone (separate process from the API Host)
```

Target a single test project directly when needed (e.g. `dotnet test tests/Project.Domain.UnitTest`); `ls tests/` lists them — no Trait annotations required. **Gotcha:** the dev Aspire dashboard runs at `http://localhost:15278`; when started from a terminal, use the printed `/login?t=...` URL on first browser visit.

Container builds intentionally mirror the repo-root layout inside the SDK stage (`src/Project.*` under a non-`/src` working directory — the root `Dockerfile` uses `WORKDIR /build`, so `dotnet restore` logs clean `src/Project.*` paths, never `/src/src/Project.*`). When editing `Dockerfile`, keep `Project.slnx`, `Directory.*.props`, `NuGet.Config`, and `src/` in their repo-root-relative positions so solution/project references and central package props continue to resolve. `.github/workflows/publish-image.yml` pushes the GHCR image from the repo-root `Dockerfile` (push to `main` → `:latest`, `v*` tags → semver tags, `workflow_dispatch` → a supplied pre-release version, never `:latest`). **Gotcha:** `workflow_dispatch` inputs support only `description`/`type`/`required`/`default`/`options` — a `pattern:` key makes GitHub reject the whole workflow file, so the semver shape of `inputs.version` is enforced by a fail-fast `Validate dispatch version` step instead; see `.docs/wiki/ci.md`.

## Test Framework

xunit.v3 · Shouldly · Bogus · Respawn. Three tiers (the distinction is non-obvious and drives where a test belongs):

- **L0** `*.UnitTest` — no I/O, all in-process.
- **L1** component — `Application.ComponentTest` uses in-memory EF Core; `Infrastructure.ComponentTest` uses a real isolated DB + Respawn.
- **L2** `*.IntegrationTest` — full stack, real PostgreSQL.

Shared fixtures live in `tests/Project.TestFramework/`; the Aspire dependency host (PostgreSQL + WireMock containers) in `tests/Project.TestFramework.Aspire/`. See `.docs/wiki/testing.md`.

## Style and Dependencies

Authoritative stack and coding conventions for AI coders are in `.agents/rules/project-overview.instructions.md` and backend-specific rules under `.agents/rules/backend/` (scoped per-file via `**/*.cs` frontmatter).

## Architecture Decisions (NFRs)

Human-facing reviewer documentation lives in `.docs/wiki/`. Detailed high-level designs, non-functional requirements, and lightweight architecture decision records live under `.docs/hlds/`.

## CI/CD

PR gate — `.github/workflows/pr-gate.yml` (triggers: `pull_request` → `main`, `push` → `main`, `workflow_dispatch`): restore → build (Release) → Aspire-backed test with coverage via the local action `.github/actions/aspire-test-with-coverage`, then publish + upload the coverage report. Full step list, service ports, timing, and local .NET tools: `.docs/wiki/ci.md`.

Skill security gate — `.github/workflows/skill-scan.yml` (triggers on changes to `.agents/skills/**`, the workflow, the report script, or the baseline): scans AI agent skills with [NVIDIA SkillSpector](https://github.com/NVIDIA/SkillSpector) (pinned commit; non-blocking warning when upstream `main` moves past the pin). **Baseline-aware gate, not a raw-score gate.** These are first-party skills that legitimately run shell/`gh`/`git`/template operations, which SkillSpector (correctly, for an untrusted third party) rates HIGH — so its raw risk score is pinned at 100 (exit `1`) by design. The gate decision therefore comes from `.github/scripts/skillspector-report.py`, which subtracts the accepted findings listed in **`.github/skillspector-baseline.yml`** (each entry matched by `(id, file)` and carrying a written justification) and **fails only on ACTIVE, non-baselined findings**; a scan error (exit `2`) still hard-fails. A genuinely new dangerous pattern (real exfiltration, hidden instructions, supply-chain) is not baselined, so it still blocks the PR — adding a finding to the baseline is a reviewed, justified act, never a blanket mute. **Scan-mode policy (A):** the gate keys off a **deterministic static scan (`--no-llm`)** whose baseline-aware decision is authoritative; the LLM semantic stage is nondeterministic across model/prompt drift, so it runs as a **separate non-blocking advisory scan** whose findings are rendered in the run summary for human review and **never affect the gate decision** (see `.agents/skills/AGENTS.md`, LADR-001). The report script derives a findings report (raw score + **Active** and **Accepted/baselined** tables, plus stale-entry detection) and, when the advisory LLM report is present, a clearly-labeled **non-gating** advisory section — all written to the **Actions run summary** on every run, plus a SARIF file (from the gating static scan; baselined findings marked `suppressions`) published to the **Security → Code scanning** tab (requires GitHub Advanced Security / Code scanning enabled — otherwise the run summary is the place to read findings). Skills that need a secret must follow `.github/instructions/skills/skill-secret-handling.instructions.md` (read it from the runtime env via a script; never embed the value). The advisory LLM scan runs when the API key is present and self-skips otherwise. Provider config comes from org/repo settings: variables `SKILLSPECTOR_PROVIDER` (default `openai`), `SKILLSPECTOR_MODEL` (bare model id), `SKILLSPECTOR_OPENAI_BASE_URL` (OpenAI-compatible base, must end at `/v1`), and secret `SKILLSPECTOR_OPENAI_API_KEY`.

## Git Constraints

This repository is hosted on **GitHub** at `https://github.com/generic-automation-and-it/project`.

- **CLI tool:** Use `gh` (GitHub CLI) for PR and repository operations.
- **PR template:** `.github/pull_request_template.md`
- **Code owners:** `.github/CODEOWNERS` — all files owned by `@generic-automation-and-it/project`

## Glossary

<!-- TODO: Add domain-specific terms and abbreviations as the project evolves. -->

| Term | Description |
|---|---|
| Blueprint | A reusable, parameterised specification for a component or service |
| Catalogue | The collection of all blueprints and templates in this repository |
| Spec-driven | Development approach where machine-readable specifications are the source of truth |
