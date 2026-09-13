---
description: 'How AI agent skills must handle secrets — read from the runtime environment via a script, never embed secret values in model-visible or committed text.'
globs: ".agents/skills/**"
paths:
  - ".agents/skills/**"
applyTo: '.agents/skills/**'
alwaysApply: false
---

# Skill Secret Handling

How any skill under `.agents/skills/` must handle a secret (API key, token, password, connection string). Updated: 2026-06-21

## The Rule

A skill that needs a secret **MUST delegate to a script that reads the secret from the runtime environment** (an environment variable injected at execution time) and uses it there. The secret **value** must never appear in any model-visible or committed text.

| Allowed | Forbidden |
|---------|-----------|
| `SKILL.md` instructs the agent to run a script that reads `$MY_API_KEY` from the env | A real key, token, or password written literally in `SKILL.md`, a prompt, agent YAML, README, reference doc, or any committed file |
| A bash/python script reads the secret via `os.environ` / `"$VAR"` and passes it to the tool | Echoing/printing the secret, putting it in a URL query string, or passing it as a logged CLI argument |
| Documenting the env var **name** the script expects (e.g. `MY_API_KEY`) | Documenting the env var **value** |

The secret value flows: **runtime environment → script → tool**. It is never typed into a file an agent reads, generates, or commits.

## Reference Pattern

`.github/workflows/skill-scan.yml` is the canonical example: the SkillSpector LLM key lives in `secrets.SKILLSPECTOR_OPENAI_API_KEY`, is injected as the `OPENAI_API_KEY` env var on the scan step, and is consumed only by the scan process. No file in the repo contains the value. Mirror this shape for any skill that needs a secret: declare the env var name, read it in a script, never persist it.

## Current Status

**One skill handles real secrets today:** `ai-asset-sync` (env-only — `OPENCODE_<PROVIDER>_API_KEY` via opencode `{env:…}` placeholders, `GITHUB_TOKEN` via `gh` env auth; no value ever appears in committed text or prompts). The only SkillSpector "data exfiltration / context leakage" signal ever raised on this tree was a false positive on a natural-language prompt phrase (no secret value, no external send), since reworded. This rule is a **standing guardrail** so that if a future skill needs a secret, it is added the safe way — and so the SkillSpector gate's exfiltration detection stays meaningful rather than being trained to ignore real leaks.

## Changelog

> AI loading note: Skip this section during routine task execution. Use it only when updating this rule file.

| Date | Change |
|:-----|:-------|
| 2026-09-13 | Moved into the new `skills/` rule category (with `skillspector-pre-pr`); cross-references updated. |
| 2026-06-21 | Initial version — env-via-script secret handling for skills; mirrors the skill-scan workflow's key handling. |
