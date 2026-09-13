# AI Asset Sync

Dependabot-style reconciler for AI assets (skills, rules). A scheduled workflow checks `.github/assets/ai-sync.yml`, uses OpenCode as an AI-DevEx expert to merge upstream changes with local adaptations, and opens one chore PR per run when the tree differs.

Implementation lives in `.agents/skills/ai-asset-sync/scripts/run-sync.sh`. The reusable workflow and composite action are thin wrappers — change sync behaviour in the script.

## Consumer setup

1. Copy [`.docs/examples/ai-asset-sync-caller.yml`](../examples/ai-asset-sync-caller.yml) to `.github/workflows/pipeline-ai-asset-sync.yml`.
2. Add `.github/assets/ai-sync.yml`:

```yaml
version: 1
entries:
  - source: generic-automation-and-it/smooth-devex-template@main:.agents/skills/ai-brain-dump
  - source: generic-automation-and-it/smooth-devex-template@v1:.github/instructions/git
    strategy: overwrite
```

3. Set the selected provider's `OPENCODE_<PROVIDER>_API_KEY` secret and (recommended) pin `OPENCODE_CLI_VERSION`.
4. Optional Variables: `OPENCODE_AI_SYNC_PROVIDER` (default `GEMINI`), `OPENCODE_AI_SYNC_MODEL_PRIMARY` / `_SECONDARY`, `OPENCODE_AI_SYNC_CONFIG`.

Same-org callers may use `secrets: inherit`. Cross-org callers must map keys explicitly (GitHub rejects cross-org inherit).

## Triggers

Consumer side: `schedule` (cron) + `workflow_dispatch` only. The reusable workflow itself is `workflow_call` + `workflow_dispatch` (no push/pull_request).

## What happens on a run

| Situation | Model? | Files? | PR? | Lockfile |
|-----------|--------|--------|-----|----------|
| Upstream SHA == lockfile | no | no | no | unchanged |
| Local missing or `strategy: overwrite` | no | copy upstream | yes if diff | advances in the PR |
| Local present, mergeable | yes | merged/applied | yes if diff | advances in the PR |
| Heavy divergence | yes | **untouched** | yes only if *other* entries changed | that entry not advanced |
| AI says local already equivalent | yes | no | **no** | unchanged (re-analyse next run) |

Branch: `chore/ai-sync-{UTC YYYYMMDD-HHMM}-{run id}` (fresh each run, collision-safe). Title: `chore[NO-TICKET]: sync AI assets` (override: `pr_title` input / `AI_ASSET_SYNC_PR_TITLE`). Body: repo PR template + provenance table + Conflicts / Gaps / Issues / Blockers.

## Packaging

| Shape | When |
|-------|------|
| Reusable `workflow_call` | Caller YAML in `.docs/examples/ai-asset-sync-caller.yml`. Skill fetched at `github.job_workflow_sha` if not installed locally. |
| `workflow_dispatch` in this template | Same workflow file, in-repo skill, no side checkout. |
| Skill installed locally | Skip side checkout; `run-sync.sh` from the consumer tree. |
| Composite action `.github/actions/ai-asset-sync` | Copy-install / local-job packaging; still calls `run-sync.sh`. |

## Auth and limitations

`GITHUB_TOKEN` only (open source). Known GitHub restriction: PRs opened with `GITHUB_TOKEN` do **not** trigger downstream `pull_request` workflows (your PR gate will not run on the sync PR). Re-run checks after review.

Private source repos work only where that token can read them (same repo/org). Cross-org private sources are out of scope. No PAT / GitHub App token.

## Non-goals

Move/rename (remote path ≠ local path), one-PR-per-entry, auto-merge of the sync PR.

## Related

- Skill: `.agents/skills/ai-asset-sync/`
- Example caller: `.docs/examples/ai-asset-sync-caller.yml`
- [CI](ci.md) · [AI tooling](ai-tooling.md)
