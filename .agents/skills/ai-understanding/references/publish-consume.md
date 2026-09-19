# Publish / Consume Contract

Export writes a session's knowledge to the working store; **publish** carries it out of the workspace
altogether, and **consume** brings another workspace's archive in. The working store
(`.context/understandings/`) is gitignored and dies with the workspace, so publishing is how knowledge
survives and consuming is how a fresh workspace starts with knowledge it did not earn.

The store is never shared through the repository (LADR-008). Nothing published reaches git; the
durability boundary is the archive a human keeps.

## Two tiers

| Tier | Path | Tracked | Lifetime | Purpose |
|------|------|---------|----------|---------|
| Working memory | `.context/understandings/<subject>-<yyyyMMdd-HHmm>/<slug>.md` | No | This workspace | Where export lands — one stamped folder per export run; a slug repeated across folders is a version chain, newest current |
| Published archive | `.context/understandings-publish/understandings-<YYYYMMDD-HHMMSS>.zip` by default, or `--path` when given | No | Whoever keeps the file | A snapshot of the store, mailed, dropped in a channel, or copied to a stick |

Nothing is published implicitly — it takes the `--publish` invocation. No approval prompt gates the
write itself: the invocation, and an explicit `--path` if given, is the consent, and the report after
writing (step 7) is what a human reviews.

## What travels

| `scope` | Published by default | Meaning |
|---------|---------------------|---------|
| `portable` | Yes | True of the stack, tooling, or language anywhere it is used |
| `repo-specific` | Yes (excluded with `--portable-only`) | True only of this repository's setup, data, or conventions |

Publishing to another repository is what `--portable-only` is for. Getting it wrong in the permissive
direction is the expensive failure: a `repo-specific` Understanding published and then consumed
elsewhere is a local quirk presented to a future agent as firsthand universal knowledge, with
provenance that makes it look trustworthy.

When the distinction is genuinely unclear, mark it `repo-specific` at export time — declaring `scope`
correctly while the evidence is fresh is what lets `--portable-only` filter safely later. The cost of
leaving knowledge behind is one rediscovery. The cost of shipping a false universal is every consumer
acting on it.

## Publish

1. Read the working store's index; select every unit, or only `portable` units with `--portable-only`.
2. No approval needed — the default archive path, or an explicit `--path`, is the consent. Step 7 reports the slug list and the path after writing.
3. Archive each `<subject>-<yyyyMMdd-HHmm>/<slug>.md`, plus its `<slug>.assets/` when it has one. Filter per Understanding, never per subject — one subject routinely mixes scopes. Subject folders keep their stamp verbatim: publishing never re-stamps, because the stamp records when the knowledge was learned and the archive name already records when it was sent.
4. When `--portable-only` excludes a unit that an archived unit's `links` or `provenance.inherited` names, drop the brackets around that `[[slug]]` in the archived copy and keep the entry — the same convention the store uses for a pruned ancestor. Without `--portable-only` every unit is present and the case cannot arise.
5. On each archived copy, set `provenance.published_from` and leave the working copy untouched.
6. Regenerate an `INDEX.md` inside the archive covering only the archived units, using the index script against the staged tree.
7. Write the zip to `.context/understandings-publish/`, or to `--path` when given — never inside `.context/understandings/`, where the index generator would read it as a subject folder — and print the count, the path, and the slugs.

### Pre-publish check

Understandings are written during debugging, when a literal value is the fastest thing to type. Before
anything leaves the workspace, confirm no unit carries a credential, token, connection string, or
internal hostname. Record the shape of the problem, not the value. See
`.github/instructions/skills/skill-secret-handling.instructions.md`.

## Consume

The source is a local path to a published archive — always positional; `--path` overrides only the
target store it unpacks into (default `.context/understandings/`), never the source. How the archive
arrived — mail, chat, a shared drive — is out of band. **This skill does not fetch remote content**, and
`ai-asset-sync` does not transport Understandings. No approval prompt gates the unpack: the source path
is the consent, and the reconciliation table below is reported per slug after writing.

A zip is untrusted input. Refuse any entry whose resolved path escapes the target store (`..` segments,
absolute paths, symlinks), and reject the whole archive with a clear message rather than unpacking part
of it.

Reconcile per incoming slug. The key is the slug, and an incoming copy **keeps its own stamped folder**:
under LADR-010 the same slug in two folders is a version chain, not an index failure, so there is nothing
left to merge away:

| Incoming slug | Action |
|---------------|--------|
| Absent locally | Copy it in under its incoming stamped folder; set `provenance.consumed_from` (the archive name); set `confidence: observed` |
| Present, same question, **older** incoming stamp | Copy it in as an older version. It lands as history, unlisted; the local copy stays current. Report it |
| Present, same question, **newer** incoming stamp | Copy it in, but **ask before letting it become current** — this is the one consume outcome that changes what this workspace believes. Show both claims and recommend nothing by default; the local copy was verified here, the incoming one was not |
| Present, different question | Bring it in under a slug disambiguated by what distinguishes it |

Two rules make consuming safe to run without reading every incoming file first:

- **Local belief is never silently replaced.** Consuming adds copies and surfaces disagreements; the one
  case that would flip which copy an agent reads is gated on an explicit ask. _(This rule was once
  justified by "the same slug in two folders fails the index" — LADR-010 removed that failure, and the
  rule did not outlive its reason. It survives on its own merit: the local copy was confirmed against
  this setup, the incoming one was not.)_
- **Incoming knowledge arrives unverified.** It was `verified` somewhere else, against a setup that may
  differ. It becomes `verified` here only when something here confirms it.

Because folders are stamped, two workspaces that picked the same subject name almost never share a
folder name, so the common outcome of a consume is *add*, and the version rows above fire on the slug
alone.

After reconciling, regenerate the working index.

## Lifecycle

```
session → .context/understandings/<subject>-<yyyyMMdd-HHmm>/<slug>.md   (--export, one folder per run; newest copy of a slug is current)
        → .context/understandings-publish/understandings-<stamp>.zip     (--publish, per-unit scope filter)
        → handed over out of band                                        (mail, chat, drive)
        → .context/understandings/<subject>-<yyyyMMdd-HHmm>/<slug>.md   (--consume, into that workspace's store)
        → session                                                        (--import, matched by question)
        → *AGENTS.md  or  .github/instructions/                          (--promote, when it stops being an observation)
```

Promotion is the exit from this loop. An Understanding that has been consumed, confirmed, and applied
across many tasks is no longer discovered knowledge in flight — it belongs in a context file or a rule,
where it loads without anyone invoking a skill.
