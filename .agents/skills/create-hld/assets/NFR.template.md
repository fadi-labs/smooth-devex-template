# NFR-01: <Attribute>

**Status:** Draft

<!-- BEFORE WRITING THIS FILE, apply the specificity test:
     "Would this read the same for any other feature in this repo?"
       YES → delete the file ONLY IF a documented repo rule or ADR already binds the concern
             (typical examples: i18n coverage, keyboard operability, structured logging, HTTPS,
             "write tests", "no secrets in code"). Repeating a documented standard here dilutes
             the NFRs that matter. If nothing in the repo covers it, keep it — or raise it as a
             repo-wide standard instead.
       NO  → keep it. This design puts an unusual demand on the attribute: a specific latency budget
             under a named load, a migration that must not lose a specific field, a contract that
             must not break a named consumer.

     One quality attribute per file. Budget ~200 words. Expect 2–4 NFRs in an HLD, not a checklist
     of every attribute that exists. Status lifecycle: Draft → Prototype → Accepted. -->

## Requirement

<The measurable target, and the condition it holds under. Vague NFRs ("fast", "reliable") are
forbidden — pick a number or a binary assertion. e.g. "p95 added latency ≤ 25 ms on cache hit at
50 rps" / "every persisted placement value survives the migration byte-identical".>

## Verification

<How this is proven — a mechanism, not a hope. Say what must be measured or asserted; leave the
test's construction to the implementer. "A repeatable benchmark with a sample large enough to be
stable, gated in CI" beats prescribing warm-up counts and concurrency levels.>

## Acceptance Criteria

- <Observable condition that means this NFR is satisfied — the definition-of-done.>

## Applies To

<Which goals, containers, or flows this cuts across, by name — e.g. "Goal 1; the API-gateway container".>
