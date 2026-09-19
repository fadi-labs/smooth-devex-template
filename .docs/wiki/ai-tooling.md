# AI Tooling

## Approach

The development of this solution deliberately demonstrates an AI-agnostic approach to developer tooling. The goal was not to pick a favourite — it was to understand what each tool and its underlying models are genuinely best suited for across a real delivery.

## Tools Used

| Tool | Primary Role |
|---|---|
| **Claude Code** (Anthropic) | Spec-driven generation, architectural reasoning, primary code authoring |
| **OpenAI Codex** | Code generation, pull request workflow automation, agentic task execution |
| **GitHub Copilot** (web agent) | In-editor assistance, agentic task execution, pull request review participation |

All three tools share a common context through the `.agents/` folder — rules, conventions, and prompt templates are maintained in one place and symlinked per tool.

## Key Findings

- Cross-model review (writing with one tool, reviewing with another) caught assumptions and patterns the authoring model would have missed.
- Claude Code performed strongest on spec-to-code generation when given structured HLDs and NFRs.
- Codex was well-suited to PR workflow automation and repetitive generation tasks.
- GitHub Copilot's web agent added value in PR review participation — visible in the PR conversation history.

## Embedded AI Agent

A Claude SDK-powered conversational agent is embedded directly in the API. It allows natural-language queries against the buildability data — for example: *"Which sets can brickfan35 build?"* — rather than requiring direct API calls. This was a deliberate side quest to explore agentic integration as a pattern for data-rich APIs.

## Recommendations (for teams adopting this approach)

- Run AI reviews alongside linters — they serve different purposes.
- Use a different model for review than for authoring. Cross-model review is more effective.
- Invest in shared context files (`.agents/` equivalent) early. All tools benefit from a single source of truth on conventions and domain knowledge.

## Setup

See the `.agents/` folder for full configuration. Run the appropriate setup script after cloning to recreate symlink aliases:

```bash
# Mac / Linux
bash .agents/setup/scripts/agents-setup.sh

# Windows (PowerShell — run as Administrator)
.\.agents\setup\scripts\agents-setup.ps1
```

## AI asset sync

Scheduled OpenCode reconciler for skills/rules. Consumer manifest `.github/assets/ai-sync.yml`, reusable workflow + composite action, skill entrypoint `.agents/skills/ai-asset-sync/scripts/run-sync.sh`. See [AI Asset Sync](ai-asset-sync.md).

## Understandings

Agent memory as a reviewable artifact. An *Understanding* is a distilled unit of discovered knowledge — a non-obvious root cause, an environment quirk, a convention invisible in the code — written so a future agent with none of the originating context can act on it.

They accrue locally in `.context/understandings/<subject>-<yyyyMMdd-HHmm>/<slug>.md` (gitignored — a stamped folder is one export run, holding only what that run produced). A slug addresses the knowledge rather than one copy of it, so the same slug across several stamped folders is a **version chain**: the newest stamp is what `INDEX.md` lists and what an agent reads, and older copies stay on disk as immutable history. An export that improves nothing writes nothing. They never reach the repository: a publish writes a zip under `.context/understandings-publish/` that mirrors the store, sharing is sending someone that archive, and `--consume` unpacks it into their own store. By default the archive carries every unit — pass `--portable-only` to publish just the units marked `scope: portable`, when the destination is another repo. That split is the point: encoding stays cheap enough that agents propose freely, and review happens once, at publish, when it is clear which knowledge held up.

Understandings are evidence, not orders — a rule always wins a conflict, and an Understanding contradicted by the code is flagged rather than applied. Skill: `.agents/skills/ai-understanding/`; governance: `.agents/rules/meta/understandings.instructions.md`.

## Registering agentic files in `Project.slnx`

`Project.slnx` lists every tracked agentic file **individually** — rules, skill files, scripts, assets,
references and wiki pages each get their own `<File Path="…" />` line inside a matching `<Folder>` block.
The solution format has no glob, so a file you add is invisible in the solution tree until you add the
line. Nothing enforces this: no build step, no CI check, and no test fails when a file is missing. It
surfaces as a review comment, or not at all.

Two things to get right:

- **Use the `.agents/rules/…` alias for rules**, not `.github/instructions/…`. `.agents/rules` is a
  symlink to the real directory, and the manifest is written against the alias.
- **Put the entry in the `<Folder>` block that matches its directory.** The folder blocks mirror the
  on-disk tree; a `<File>` in the wrong block shows up in the wrong place in the IDE.

**The manifest is not exhaustive today, so do not treat it as authoritative.** As of this writing 78 of
the 107 agentic files are registered. The 29 that are not are mostly per-skill `AGENTS.md` files (14 of
them), plus assorted `references/`, `assets/` and `scripts/` entries — pre-existing drift, not a
deliberate exclusion. Every registered path does resolve, so there are no dead entries.

The practical rule is **register what you add** rather than reconciling the whole tree. To check the
folder you are working in:

```bash
# Files on disk vs files registered, for one subtree
diff <(find -L .agents/skills/<skill-name> -type f -not -path '*__pycache__*' | sort) \
     <(grep -o 'Path="[^"]*"' Project.slnx | sed 's/Path="//;s/"//' \
       | grep '^\.agents/skills/<skill-name>/' | sort)
```

A `<` line is a file you still need to register; a `>` line is an entry pointing at something that no
longer exists.

## Further Reading

- [Architecture](architecture.md) — solution structure and design decisions
- [Testing Strategy](testing.md) — test levels and infrastructure
