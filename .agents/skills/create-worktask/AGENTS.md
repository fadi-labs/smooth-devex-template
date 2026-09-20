# create-worktask — AGENTS.md

## TL;DR

Authoring skill for worktask files under the gitignored `.context/work-tasks/`. The skill carries the *judgment* (which contexts to verify, what requirements and acceptance criteria to capture); `scripts/scaffold-worktask.sh` only lays down the deterministic skeleton from `assets/WORKTASK.template.md`.

## Non-Negotiables

- **Trigger semantics changed when this replaced the hook — keep the `description` imperative-shaped.** `.agents/hooks/worktask-create.sh` fired on a regex anchored to an imperative opening, so a *question* about worktasks stayed silent. A skill is selected by its `description`, so that carve-out now lives in the description text ("Does NOT trigger on questions about how worktasks work"). Loosening it to bare keywords brings back the false-fire the hook's regex was anchored to prevent.
- **The worktask contract must stay in sync with the process template.** `SKILL.md`'s "Output structure" mirrors `.agents/templates/AI_WORKTASK_PROMOTE_STANDALONE_TEMPLATE.md`'s Execution Profile block field-for-field. Changing a field there (model / path / subagents / commits / push) means changing it here **and** in `assets/WORKTASK.template.md` — three files, one contract.
- **Two `Commits` defaults must agree.** The template defaults to *not allowed* and the asset ships `not allowed`. A change that makes the asset default to allowed re-creates the autonomous-commit defect removed on 2026-09-20 — under `defaultMode: bypassPermissions` nothing else stops it.
- **No HTML comments in `assets/`.** SkillSpector rates comments in skill assets `P2` "Hidden Instructions"; `create-hld/assets/*` carries four baselined entries for exactly this. This skill deliberately keeps its asset comment-free so it needs no baseline entry — authoring guidance lives in `SKILL.md`, read every invocation. Adding a comment to the asset requires a justified `.github/skillspector-baseline.yml` entry in the same PR.

## Key Behaviors

- **Output is gitignored.** `.context/` is excluded in `.gitignore:406`, so worktasks are per-workspace and never reviewed. That is why the skill's quality bar is a checklist inside SKILL.md rather than a CI gate — nothing downstream validates a worktask.
- **The scaffolder refuses to overwrite** an existing `<slug>.md` without `--force`, because a worktask may already be mid-execution. `create-hld`'s scaffolder hard-fails instead; the `--force` escape exists here because worktask slugs are chosen by the agent and collide more easily than a zero-padded index.
- Complexity tier is **high** (`claude: opus`): the worktask is the input the entire Odin→Bragi workflow runs on, so its gaps propagate through all nine phases. It is investigation + requirement authoring, not a scripted file operation.
- Placeholders substituted by `sed` are only `{{TITLE}} {{SLUG}} {{DATE}}` — any other `{{...}}` in the asset survives verbatim into the scaffolded worktask.

## Changelog

| Date | Change | Ref |
|:-----|:-------|:----|
| 2026-09-20 | Initial version — replaces the `worktask-create.sh` UserPromptSubmit hook (Claude-only) with a skill all four runners can invoke. Hook deleted, `settings.json` registration removed. | |
