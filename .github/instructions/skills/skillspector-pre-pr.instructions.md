---
description: 'Pre-PR SkillSpector gate: when changing .agents/skills/**, run/predict the static scan and ship baseline updates in the SAME PR — never discover findings post-push'
globs: ".agents/skills/**,.github/skillspector-baseline.yml"
paths:
  - ".agents/skills/**"
  - ".github/skillspector-baseline.yml"
applyTo: '.agents/skills/**,.github/skillspector-baseline.yml'
alwaysApply: false
---

# SkillSpector Pre-PR Handling

The skill-scan gate (`.github/workflows/skill-scan.yml`) fails on any ACTIVE (non-baselined) static finding. It is baseline-diff by design, so **almost every skill change trips it on the first CI run** unless findings are anticipated. Handle them BEFORE commit/push, not as a post-PR fixup loop.

## Mandatory pre-commit steps when touching `.agents/skills/**`

1. **Predict findings.** Scan your diff for the static analyzer trigger classes below. Each hit in a NEW file, or a NEW pattern class in an existing file, WILL produce an ACTIVE finding.
2. **Run the gate locally when possible** (mirrors CI exactly; pinned ref from `SKILLSPECTOR_REF` in `.github/workflows/skill-scan.yml`):

   ```bash
   REF=$(grep -m1 'SKILLSPECTOR_REF:' .github/workflows/skill-scan.yml | awk '{print $2}')
   python3 -m venv /tmp/skillspector-venv && /tmp/skillspector-venv/bin/pip -q install "git+https://github.com/NVIDIA/SkillSpector@${REF}"
   /tmp/skillspector-venv/bin/skillspector scan .agents/skills/ --no-llm --format json --output /tmp/skillspector.json || true
   python3 .github/scripts/skillspector-report.py /tmp/skillspector.json /tmp/skillspector.sarif .agents/skills \
     --baseline .github/skillspector-baseline.yml --decision-file /tmp/gate.txt
   cat /tmp/gate.txt   # must print: pass
   ```

   No network / install fails → fall back to prediction (step 1) and say so in the PR description.
3. **Baseline in the same commit/PR.** Every expected first-party finding gets a justified entry in `.github/skillspector-baseline.yml` (`id` + `file` + written `reason`) alongside the code that introduces it. A skill PR that will trip the gate without its baseline update is incomplete.
4. **Never gut a skill for a green gate.** If the flagged behavior is the skill's function, keep it and baseline it (repo non-negotiable — see `.agents/skills/AGENTS.md`).
5. **Id drift is normal.** A `SKILLSPECTOR_REF` bump may re-categorize findings (e.g. TM1→SC2). Re-run the local scan after any pin bump and retarget stale baseline ids in the same PR.

## Static trigger classes (what to predict)

| Class (typical ids) | Trips on |
|---|---|
| Tool/chaining abuse (TM1, TM2) | `rm`/`rm -rf`, multi-step resolve→fetch→write chains — including in DOCS text |
| External script fetch (SC2) | `curl \| bash`, remote installers |
| Subprocess (AST4, OH1) | `subprocess` in Python, even `shell=False` |
| Credential access (PE3) | literals like `/etc/passwd`, key-looking strings — even in negative TESTS |
| Hidden instructions (P2) | HTML comments in templates/markdown |
| Autonomy (EA2) | "without asking" / autonomous-mode phrasing |
| Persistence (RA2) | session/tmp state descriptions |

Baseline matching is `(id, file)` and line-agnostic: moving a flagged pattern to a NEW file needs a NEW entry even if the id is already baselined elsewhere.

## Changelog

> AI loading note: Skip this section during routine task execution.

| Date | Change | Ref |
|:-----|:-------|:----|
| 2026-09-13 | Initial version — created after repeated post-PR SkillSpector fixup loops on skill PRs (#66). | #66 |
