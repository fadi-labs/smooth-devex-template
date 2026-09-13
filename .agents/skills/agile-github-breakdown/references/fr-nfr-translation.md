# FR/NFR → acceptance criteria translation

## The rule

Every functional or non-functional requirement a Feature assigns to a Task becomes exactly one
acceptance-criterion bullet on that Task, phrased as a testable condition, with the source ID
cited in parentheses. Do not paraphrase away the measurable part.

Bad (softened, untraceable):
> - Upstream calls should be reasonably fast.

Good (testable, traceable):
> - Full lookup chain completes p95 < 5 seconds, IE action to data displayed (NFR-8).

If a requirement doesn't fit any drafted Task, that's a signal the breakdown is incomplete —
surface it rather than dropping it silently.

## The soft-tech-recommendation pattern

A Feature states outcomes; a Task may suggest an implementation approach, but never mandates one
unless the source material already forces that choice (e.g. "must use the platform's existing
secret-sync mechanism" because no alternative exists). Default phrasing:

> For example with tech stack: **<library/tool>** — team's call, not fixed by this Task.

This applies even to a technology the team has already informally converged on in conversation.
State the requirement the mechanism must satisfy (e.g. "transient failures are retried"), then
offer the example separately, so a developer who picks a different tool is still compliant.

## Worked example (anonymized)

Feature-level NFR:

> NFR-7 — Resilience. Transient upstream failures are retried. For each lookup it is defined
> whether failure is fatal to the flow or degrades it.

Translated into the Task that owns the API client:

> - Transient upstream failures are retried; for this lookup, fatal-vs-degrade behavior on
>   exhausted retries is explicitly decided (NFR-7). For example with tech stack: Polly retry
>   policies.

Feature-level decision (not itself an FR/NFR, but a scope decision from a follow-up discussion) that
needed to land on a *specific* Task rather than stay at Feature level:

> Decision: stand-in data ships as a JSON resource embedded in the application, not read from the
> database. On every app startup, the app reconciles the stub server's state against that resource.

Translated into the stub Task's acceptance criteria, split into two independently-checkable
bullets rather than one run-on sentence:

> - Stub data ships as a JSON resource embedded in the application — not read from the database.
>   Embedding mechanism (e.g. a .NET `EmbeddedResource`) is a developer decision.
> - On every app startup, the app reconciles the stub server's state against that resource: removes
>   entries no longer present, updates entries that changed, adds entries that are new — matched by
>   each stub's request/query values, not a database key.

Note what carried over exactly (the reconciliation semantics: remove/update/add, matched by
request values not a DB key) versus what got left open for the implementer (the embedding
mechanism, explicitly marked as their call).
