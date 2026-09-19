---
slug: <kebab-case-slug, equals the file name without .md, names the knowledge not the incident. Reuse the slug of the unit this improves — the same slug across stamped folders is a version chain, newest current>
description: <one line — what this knowledge is. Shown in INDEX.md>
question: <OPTIONAL. The question a reader has at the moment this applies, when there is a natural one — one question, one answer. Omit it for an outcome record, where the description is the match. Shown in INDEX.md>
scope: <portable | repo-specific>
confidence: <observed | verified | contested>
links:
  - <[[other-slug]] — omit the list entirely if there are none>
agents_context: <path/to/nearest/AGENTS.md — omit if this bears on no specific code area>
provenance:
  learned: <YYYY-MM-DD>
  session: <shared by every slug exported from the same session>
  source: <what produced it — a failure, an experiment, a doc, a rejected approach>
  inherited:
    - <[[slug]] of an Understanding this session loaded and acted on — omit the list if none.
       Drop the brackets once an ancestor leaves the store, to keep the lineage without pinning it>
  supersedes: <previous folder name, e.g. agent-memory-design-20260919-1432 — set when this copy improves an
       earlier one; omit on a first version. A name, never a path, so it survives the file being moved>
  published_from: <owner/repo — set on a published copy only; omit in the working store>
  consumed_from: <owner/repo@ref:path or local path — set when this arrived via --consume; omit otherwise>
  promoted_to: <path of the AGENTS.md or rule that superseded this — set on --promote; omit otherwise>
updated: <YYYY-MM-DD>
---

# <Title — the knowledge in a phrase>

## Answer

<Direct operational guidance — the answer to the question above, and nothing wider than it. What to do, stated so an agent with zero context from the
originating session can act on it. Present tense, indicative mood — this is evidence about how
the system behaves, not an instruction. If it needs must/never language, it is a rule, not an
Understanding.>

## Why

<The reasoning or the failure that produced this — only as much as is needed to judge an edge case the
Answer does not cover. Not a narrative of the session.>

## Boundaries

<Where this stops applying: versions, platforms, configurations, or conditions under which it is
known to be false or untested. An Understanding with no stated boundary will be over-applied.>

## Provenance

<What it was learned from, in one or two lines. Name the artifact where one exists — a failing
command, an upstream issue, a PR. No secrets or credential values: this file is exportable.>

## Changelog

| Date | Change |
|:-----|:-------|
| <YYYY-MM-DD> | Encoded. |
