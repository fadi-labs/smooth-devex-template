# .agents/skills — AGENTS.md

## TL;DR

First-party AI agent skills. They legitimately run shell, `gh`/`git`, and template file operations, which the NVIDIA SkillSpector gate (`.github/workflows/skill-scan.yml`) rates HIGH for an untrusted third party — so accepted, inherent findings are **omitted from the published SARIF** via a justified allowlist, and the gate fails only on **new** findings.

## Non-Negotiables

- **Secrets go through the environment, never into text.** Any skill needing a secret MUST follow `.github/instructions/skills/skill-secret-handling.instructions.md`: a script reads the value from a runtime environment variable; the value never appears in `SKILL.md`, prompts, agent YAML, README, or any committed file. First secret consumer: `ai-asset-sync` reads `OPENCODE_<PROVIDER>_API_KEY` and `GITHUB_TOKEN` from the runtime environment only (opencode `{env:…}` placeholders + `gh` env auth) — the compliant reference implementation.
- **Never silence a SkillSpector finding by removing a skill's capability.** If the flagged behavior is the skill's actual job (shell out to `gh`, swap a symlink, refresh a template dir), keep it and add a justified entry to `.github/skillspector-baseline.yml`. A green gate bought by gutting a skill is a failure.
- **Every baseline entry needs a written `reason`.** The allowlist is auditable, not a blanket mute. A new finding id, or the same id in a new file, is not baselined and blocks the PR until reviewed.

## Architecture Decisions

### LADR-001 — Gate on the deterministic static scan; LLM semantic stage is advisory

- **Date:** 2026-06-21 · **Status:** Accepted
- **Context:** The accepted-findings baseline is built from a static (`--no-llm`) scan. When the LLM semantic stage runs (provider/model supplied via org settings), its analyzers surface **additional, nondeterministic** findings whose ids/locations are not in the static baseline. Those count as ACTIVE and fail the gate — so a model or prompt change re-breaks the gate even though no skill changed.
- **Decision:** The gate runs a **deterministic static scan (`--no-llm`)** whose baseline-aware decision is authoritative. The **LLM semantic stage runs as a separate non-blocking advisory scan** (`continue-on-error`, self-skips with no key); its findings are rendered in the job summary via `--advisory` and **never affect the gate decision**.
- **Consequences:** The gate is stable across model/prompt drift and needs no LLM key to function. Static analyzers still block real dangerous patterns (`curl|bash`, `eval`, `rm -rf`, secret exfiltration), so the gate stays meaningful. Trade-off: a *semantic-only* dangerous pattern (one no static rule catches) would surface in the advisory section for human review rather than hard-blocking. To make the semantic layer hard-block instead, gate on the LLM report and baseline its findings (accepting periodic re-triage on drift).

## Key Behaviors

- The gate decision is computed by `.github/scripts/skillspector-report.py`, not by SkillSpector's raw `risk > 50` exit code (which is pinned at 100 for first-party skills by design). The script subtracts baselined findings and fails only on active ones; a scan error still hard-fails.
- The job summary lists **Active** findings (gate-failing) separately from **Accepted (baselined)** findings, and flags stale baseline entries after a fix removes a finding.
- **`ai-understanding` never writes to the tracked tree.** Its working store is `.context/understandings/<subject>-<yyyyMMdd-HHmm>/<slug>.md` (gitignored), and `--publish` writes a zip under `.context/understandings-publish/`, also gitignored — the store is not shared through the repository. A change that makes this skill write to `.agents/understandings/` or any other tracked path turns unreviewed session observations into shared repository memory — see that skill's LADR-001 and LADR-008.
- Two scans run per CI invocation (policy A, LADR-001): a **gating static scan** (`--no-llm`, drives the decision + SARIF) and, when a key is configured, a **non-gating LLM advisory scan** rendered as a separate, clearly-labeled summary section. The baseline (`skillspector-baseline.yml`) covers only the static scan.

## Changelog

> AI loading note: Skip this section during routine task execution. Use it only when updating this rule file.

| Date | Change | Ref |
|:-----|:-------|:----|
| 2026-06-21 | Initial version — documents the SkillSpector baseline gate contract and the secret-handling guardrail for skills. | #52 |
| 2026-06-21 | LADR-001: gate on the deterministic static scan; LLM semantic stage runs as a non-blocking advisory (policy A). Resolves the static-vs-LLM baseline mismatch that failed the gate on run 27907080342. | #52 |
| 2026-09-13 | `ai-asset-sync` becomes the first skill consuming secrets (env-only: provider API key + `GITHUB_TOKEN`); status text updated from "no skill handles a real secret". | #66 |
| 2026-09-19 | `ai-understanding` added — `--export` writes a session's discovered knowledge to the gitignored `.context/understandings/` store; `--publish` to a tracked path is a separate approved step. | |
| 2026-09-19 | `ai-understanding`: publish retargeted from a tracked path to a zip under `.context/` (LADR-008); store path shows the stamped subject folder. | |
| 2026-07-31 | SARIF now **omits** baselined findings instead of marking them `suppressions`; the code-scanning check was red because the back end did not honor SARIF suppressions. Summary "Accepted (baselined)" section is unchanged (reads the scan output). | |
| 2026-09-20 | `create-worktask` added, replacing the Claude-only `worktask-create.sh` hook. Its `assets/` template is deliberately HTML-comment-free so it needs no `P2` baseline entry — unlike `create-hld/assets/*`, whose four entries are the precedent. | |
