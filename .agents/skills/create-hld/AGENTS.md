# create-hld — AGENTS.md

## TL;DR

Authoring skill for design-only HLD folders under `.docs/hlds/NNN-<slug>/`. The skill carries the *judgment* (what intent/decisions/NFRs to write); `scripts/scaffold-hld.sh` only lays down the deterministic skeleton from `assets/` templates.

## Non-Negotiables

- **Two AGENTS.md quality contracts exist — do not cross them.** `scripts/hld-agents-rules.sh` is the *HLD variant* (no architecture section — diagrams live in `diagrams/`). The repo-wide `.github/instructions/meta/knowledge-conventional-contexts-quality.instructions.md` keeps its System Context section. A scaffolded HLD's AGENTS.md follows the script, not the repo-wide rule.
- **Output dir is `.docs/hlds/` (plural)** to match the repo's documented HLD location (root `AGENTS.md`). The upstream source used singular `.docs/hld/`; if syncing changes back, keep plural here.
- **Templates are placeholder-substituted by `sed`**, not by an agent. Only `{{INDEX}} {{SLUG}} {{SLUG_UPPER}} {{TITLE}} {{TITLE_MERMAID}} {{DATE}}` are substituted — any other `{{...}}` in an asset survives verbatim into the scaffolded file. `{{TITLE_MERMAID}}` is the title with `"` encoded as `#quot;`, for use inside double-quoted Mermaid string literals. Titles with control characters are rejected up front.
- **The budgets and the two tests (specificity, line) live in SKILL.md, not in a reference file.** They are read every invocation; moving them behind a `references/` load makes them skippable, which defeats them.

## Key Behaviors

- The index is `max(existing NNN)+1`, computed by globbing `.docs/hlds/[0-9][0-9][0-9]-*/`. A non-conforming folder name (no 3-digit prefix) is silently ignored, so a stray dir won't shift numbering.
- Scripts are `bash` + coreutils only and discover repo root via `git rev-parse` — no Claude-specific behaviour, so Codex/Copilot/Cursor run them identically. Both must stay executable (`chmod +x`).
- Complexity tier is **high** (`claude: opus`): multi-turn clarification gates + architectural judgment, unlike the script-driven low-tier skills.

## Changelog

| Date | Change | Ref |
|:-----|:-------|:----|
| 2026-06-16 | Initial version — ported from upstream `create-hld`, made project-agnostic (Linear→tracker, `.docs/hld`→`.docs/hlds`, dropped historical TEMPLATE_HLD.md and repo-specific reference HLDs). | |
| 2026-09-13 | Ported the economy bar from downstream create-hld: word budgets, NFR specificity test, line test, requirement-not-recipe, cut pass, `Alternatives Considered` dropped — kept `.docs/hlds/`, tracker-agnostic wording, and repo hook references. | |
