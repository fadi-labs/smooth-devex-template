---
name: ai-asset-sync
description: Dependabot-style sync of AI assets (skills, rules) from owner/repo@ref:path sources. Installs OpenCode CLI, AI-merges local vs upstream, and opens a chore PR when the tree differs. Trigger on "sync AI assets", "ai-asset-sync", or the GitHub Action/workflow wrappers.
allowed-tools:
  - Bash(.agents/skills/ai-asset-sync/scripts/run-sync.sh:*)
  - Bash(.agents/skills/ai-asset-sync/scripts/lib/*)
  - Bash(git:*)
  - Bash(gh:*)
  - Bash(python3:*)
models:
  claude: opus
  copilot: auto
  codex: gpt-5.5
---

# AI Asset Sync — Skill

Scheduled / on-demand reconciler for AI assets (skills under `.agents/skills/`, rules under `.agents/rules/` or `.github/instructions/`). **Not** a blind copy: OpenCode acts as an AI-DevEx expert, merges when safe, and reports blockers instead of clobbering.

CI packaging (composite action + reusable workflow) calls **`scripts/run-sync.sh`** — the same entrypoint you run locally. Two packagings, one implementation.

## TL;DR

1. Consumer lists sources in `.github/assets/ai-sync.yml` (`owner/repo@ref:path`, remote path == local path).
2. Lockfile `.github/assets/ai-sync.lock` records last-synced SHA; unchanged SHA → skip, no model.
3. Changed entries: overwrite or AI-merge. Blocker → leave local untouched.
4. Any file diff → one PR on `chore/ai-sync-{datetime}-{runid}`, title `chore[NO-TICKET]: sync AI assets` (override via `--pr-title` / `AI_ASSET_SYNC_PR_TITLE`), PR template + provenance/conflicts sections.
5. No diff → no PR. Lockfile does not advance without a PR.

## Local / agent use

```bash
bash .agents/skills/ai-asset-sync/scripts/run-sync.sh \
  --manifest .github/assets/ai-sync.yml \
  --dry-run
```

**The script itself does NOT default to dry-run** — invoked bare it will commit, push, and open a PR. When running interactively for a user, ALWAYS pass `--dry-run` unless the user explicitly asked to open a PR.

| Flag | Meaning |
|------|---------|
| `--manifest` | Path to YAML manifest (default `.github/assets/ai-sync.yml`) |
| `--lockfile` | Path to lockfile (default `.github/assets/ai-sync.lock`) |
| `--dry-run` / `--no-pr` | Analyse, write summary, do not commit/push/PR |
| `--entries-filter` | Comma/newline substring filter on `source` or `path` |
| `--model` | Override `OPENCODE_AI_SYNC_MODEL_PRIMARY` |
| `--repo-root` | Consumer repo root (default git toplevel) |
| `--pr-title` | PR title/commit subject (default `chore[NO-TICKET]: sync AI assets`) |

## Manifest

```yaml
version: 1
entries:
  - source: generic-automation-and-it/smooth-devex-template@main:.agents/skills/ai-brain-dump
  - source: generic-automation-and-it/smooth-devex-template@main:.github/instructions/git
    strategy: overwrite
```

- `source`: `owner/repo@ref:path`. `ref` = branch, tag, or SHA.
- `strategy`: `ai-merge` (default) or `overwrite`.
- No destination field — path in the source repo is the path in the consumer.

## Env contract (CI)

| Kind | Name |
|------|------|
| Variable | `OPENCODE_AI_SYNC_PROVIDER` (default `GEMINI`) |
| Variable | `OPENCODE_AI_SYNC_MODEL_PRIMARY` / `OPENCODE_AI_SYNC_MODEL_SECONDARY` |
| Variable | `OPENCODE_CLI_VERSION` (pin the CLI; unset = latest) |
| Variable | `OPENCODE_AI_SYNC_CONFIG` (optional custom `opencode.json`; must keep `{env:OPENCODE_*}` placeholders) |
| Secret | `OPENCODE_<PROVIDER>_API_KEY` — only the selected provider's key is read |
| Token | `GITHUB_TOKEN` — clone/read same-org sources, push branch, open PR |

Allowed providers match the review workflow: `GEMINI`, `COPILOT`, `OPENAI`, `ANTHROPIC`, `OPENCODE-GO-OPENAI`, `OPENCODE-GO-ANTHROPIC`, `OPEN_ROUTER`.

## Guardrails

- Do not move/rename assets.
- Do not open one PR per entry.
- Do not use a PAT / GitHub App token.
- Do not auto-merge the sync PR.
- Do not embed API keys in `SKILL.md`, prompts, or `opencode.json`.
