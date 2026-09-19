#!/usr/bin/env python3
"""Regenerate the Understandings INDEX.md from the subject/slug folders.

The store is `<subject>-<yyyyMMdd-HHmm>/<slug>.md`. A stamped folder is one export run; a slug
identifies the knowledge, not one copy of it, so the **same slug in several stamped folders is a
version chain** rather than an error (LADR-010). The newest stamp is the *current* version and the
rest are superseded history. `_unfiled/` is the one exempt, unstamped folder, and sorts oldest.
The index groups by subject for browsing but lists every current unit, because knowledge is
retrieved by the question it answers rather than by the subject that happened to produce it.

**Validation applies to current versions only.** Superseded copies are immutable history: validating
them would force edits to the past, and a `[[slug]]` pruned later would leave an old file permanently
invalid. Folder-level problems (an unstamped or empty subject folder, a stray unit at the store root,
the old per-unit folder shape) are reported regardless, since they belong to no single version.

A unit needing evidence artifacts (a repro, a log excerpt, a diagram) puts them in a
sibling `<slug>.assets/` directory, which is named after the slug and so cannot collide.

The index is a reference table, never a copy of the knowledge: an agent reads it to decide
which Understandings to load, then reads only those folders.

Usage:
    python3 .agents/skills/ai-understanding/scripts/understanding_index.py [store-dir]

Defaults to `.context/understandings`. Pure standard library, read/write only, no network.
Exits 1 when a current unit fails validation — the index is still written so the drift is visible.
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

DEFAULT_STORE = Path(".context/understandings")
ASSETS_SUFFIX = ".assets"
LEGACY_UNIT_FILENAME = "UNDERSTANDING.md"
REQUIRED_FIELDS = ("slug", "description", "scope", "confidence")
# `question` is optional: knowledge units carry one, outcome units match on `description` alone.
OPTIONAL_TEXT_FIELDS = ("question",)
VALID_SCOPES = ("portable", "repo-specific")
VALID_CONFIDENCE = ("observed", "verified", "contested")
UNFILED = "_unfiled"
# A subject folder is stamped with when it was created: <subject>-yyyyMMdd-HHmm, 24-hour, UTC —
# stamps from different machines must compare, so the zone is fixed rather than local. `_unfiled` is
# the one permanent catch-all and is exempt. This is a shape check, not a calendar — it accepts an
# out-of-range date/time, but not a short or long field.
SUBJECT_STAMP_RE = re.compile(r"^.+-\d{8}-\d{4}$")
# A suffix that is trying to be a stamp but has the wrong field widths, or a stamp with no subject
# in front of it. Each gets a remedy that names the actual fix instead of suggesting a second stamp.
MALFORMED_STAMP_RE = re.compile(r"^(.+)-\d+-\d+$")
STAMP_ONLY_RE = re.compile(r"^-\d+-\d+$")
# A YAML block-scalar header (`>-`, `|`, `|2-`): this parser keeps the header as the value and drops
# the indented text under it. Every field that could tempt one is specified as a single line, so the
# shape is named as a problem rather than parsed.
BLOCK_SCALAR_RE = re.compile(r"^[|>][0-9+-]{0,2}$")
# A unit past this many days without an update is worth re-reading. Outcome units — the ones
# carrying no `question`, which record what a piece of work produced — decay faster than knowledge.
STALE_AFTER_DAYS = 90
STALE_AFTER_DAYS_OUTCOME = 30


def parse_frontmatter(text: str) -> dict:
    """Parse this format: flat scalars, lists, a nested map, and a list inside that map.

    Deep enough for `provenance.inherited`; anything deeper needs extending here, not just
    the template.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    data: dict = {}
    parent: str | None = None   # top-level key holding a map or list
    child: str | None = None    # key inside that map holding a list

    for line in lines[1:]:
        if line.strip() == "---":
            break
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if not line[:1].isspace():
            key, _, value = stripped.partition(":")
            if not _:
                continue
            key, value = key.strip(), unquote(value)
            child = None
            if value:
                data[key] = value
                parent = None
            else:
                data[key] = {}
                parent = key
            continue

        if parent is None:
            continue

        if stripped.startswith("- "):
            item = unquote(stripped[2:])
            if child is not None:
                data[parent].setdefault(child, []).append(item)
            else:
                if not isinstance(data.get(parent), list):
                    data[parent] = []
                data[parent].append(item)
            continue

        key, _, value = stripped.partition(":")
        if not _:
            continue
        key, value = key.strip(), unquote(value)
        if not isinstance(data.get(parent), dict):
            data[parent] = {}
        if value:
            data[parent][key] = value
            child = None
        else:
            data[parent][key] = []
            child = key

    return data


def unquote(value: str) -> str:
    """A YAML scalar written in quotes means its content; this parser would otherwise keep the quotes.

    Matters most for `"[[slug]]"` entries: quoted, they never started with `[[`, so the reference walk
    skipped them and the lineage reader did not count them — a dangling link exited 0 and an inherited
    unit still reported as never inherited.
    """
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1].strip()
    return value


def placeholder(value: str) -> bool:
    return value.startswith("<") and value.endswith(">")


def read_unit(unit_file: Path, subject: str) -> tuple[dict | None, list[str]]:
    """Load and validate one `<subject>-<yyyyMMdd-HHmm>/<slug>.md`."""
    slug = unit_file.stem
    where = f"{subject}/{unit_file.name}"

    fields = parse_frontmatter(unit_file.read_text(encoding="utf-8"))
    if not fields:
        return None, [f"{where} has no frontmatter"]

    problems = []
    for field in REQUIRED_FIELDS:
        value = fields.get(field)
        if not isinstance(value, str) or not value or placeholder(value):
            problems.append(f"{where}: '{field}' is missing or still a placeholder")

    for field in OPTIONAL_TEXT_FIELDS:
        value = fields.get(field)
        if value is not None and (not isinstance(value, str) or not value or placeholder(value)):
            problems.append(f"{where}: '{field}' is present but empty or still a placeholder")

    updated = fields.get("updated")
    if not isinstance(updated, str) or not updated or placeholder(updated):
        problems.append(f"{where}: 'updated' is missing or still a placeholder")

    provenance = fields.get("provenance")
    if not isinstance(provenance, dict) or not provenance:
        problems.append(f"{where}: 'provenance' is missing")
    else:
        for key in ("learned", "session", "source"):
            value = provenance.get(key)
            if not value or placeholder(value):
                problems.append(f"{where}: 'provenance.{key}' is missing or still a placeholder")

    context = fields.get("agents_context")
    if isinstance(context, str) and context and not placeholder(context):
        if not Path(context).exists():
            problems.append(f"{where}: agents_context '{context}' does not exist")

    if fields.get("slug") not in (slug, None):
        problems.append(f"{where}: slug '{fields['slug']}' does not match the file name")
    if isinstance(fields.get("scope"), str) and fields["scope"] not in VALID_SCOPES:
        problems.append(f"{where}: scope '{fields['scope']}' is not one of {VALID_SCOPES}")
    if isinstance(fields.get("confidence"), str) and fields["confidence"] not in VALID_CONFIDENCE:
        problems.append(f"{where}: confidence '{fields['confidence']}' is not one of {VALID_CONFIDENCE}")

    problems.extend(inline_sequences(fields, where))
    problems.extend(block_scalars(fields, where))

    fields["folder"] = slug
    fields["subject"] = subject
    fields["path"] = f"{subject}/{unit_file.name}"
    return fields, problems


def looks_like_flow_sequence(value) -> bool:
    """True for a YAML flow sequence this parser reads as a scalar: fully `[...]`-bracketed.

    Requiring the closing bracket is what keeps prose out. A plain scalar cannot legally start
    with `[` in YAML, but this parser is lenient, and a description reading
    `[draft] how the thing behaves` is prose the writer meant — not a sequence.
    """
    return isinstance(value, str) and value.startswith("[") and value.endswith("]")


def iter_scalar_fields(fields: dict):
    """Yield every (field-path, string value) the parser produced, at both levels it supports.

    Shared by the two shape checks below. Both walk identically and both exist because this parser
    stores a value it could not really read as a plain string — so a new misread shape is a new
    predicate here, not a new traversal.
    """
    for key, value in fields.items():
        if key in ("folder", "subject", "path"):
            continue
        if isinstance(value, str):
            yield key, value
        elif isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, str):
                    yield f"{key}.{sub_key}", sub_value


def block_scalars(fields: dict, where: str) -> list[str]:
    """Catch a value written as a YAML block scalar, which this parser reads as its header.

    `description: >-` followed by an indented paragraph stores the two characters `>-` and silently
    discards the text — the index then shows `>-` and exits 0. It is the natural way to write a long
    description, so it is named rather than left to be discovered in the rendered index.
    """
    return [
        f"{where}: '{field}' is written as a YAML block scalar — this parser keeps the '{value}' header "
        f"and drops the indented text below it; put the value on one line after the colon"
        for field, value in iter_scalar_fields(fields)
        if BLOCK_SCALAR_RE.match(value)
    ]


def inline_sequences(fields: dict, where: str) -> list[str]:
    """Catch a list written in YAML flow style, which this parser reads as a plain scalar.

    `links: [[a]]` is valid YAML and looks right, but it never becomes a list, so
    `dangling_references` never walks it and an unresolvable entry exits 0. Making the parser
    read flow sequences would have to guess where `[[a]]` is one reference and where it is a
    nested sequence; naming the shape is unambiguous and the block form is what the template uses.

    Checks both levels the parser supports. A flow sequence nested in a map — `provenance.inherited`
    being the one that exists — is the same defect and was missed when only the top level was walked.
    """
    return [
        _flow_problem(where, field)
        for field, value in iter_scalar_fields(fields)
        if looks_like_flow_sequence(value)
    ]


def _flow_problem(where: str, field: str) -> str:
    return (
        f"{where}: '{field}' is written as an inline list — this parser reads block lists only, so "
        f"its [[slug]] entries are never checked; rewrite it as a block list"
    )


def load_units(store: Path) -> tuple[list[dict], list[dict], list[str]]:
    """Read every copy in the store and return (current units, superseded units, problems).

    Problems come from current versions and from the folder layout. A superseded copy's own
    validation is skipped — see the module docstring for why history is exempt.
    """
    records: list[dict] = []
    problems: list[str] = []

    for stray in sorted(store.glob("*.md")):
        if stray.name != "INDEX.md":
            problems.append(
                f"{stray.name} sits at the store root — move it to <subject>-<yyyyMMdd-HHmm>/{stray.name} "
                f"(use '{UNFILED}' when it belongs to no subject)"
            )

    for subject_dir in sorted(p for p in store.iterdir() if p.is_dir()):
        subject = subject_dir.name

        if subject != UNFILED and not SUBJECT_STAMP_RE.match(subject):
            problems.append(stamp_problem(subject))

        for legacy in sorted(subject_dir.glob(f"*/{LEGACY_UNIT_FILENAME}")):
            problems.append(
                f"{subject}/{legacy.parent.name}/ uses the old folder shape — move it to "
                f"{subject}/{legacy.parent.name}.md (artifacts go in "
                f"{legacy.parent.name}{ASSETS_SUFFIX}/)"
            )

        unit_files = sorted(subject_dir.glob("*.md"))
        if not unit_files:
            problems.append(f"{subject}/ contains no Understandings")
            continue

        for unit_file in unit_files:
            unit, unit_problems = read_unit(unit_file, subject)
            records.append({
                # The slug comes from the file name, so a copy whose frontmatter failed to parse
                # still takes part in version grouping instead of vanishing from it.
                "slug": unit_file.stem,
                "subject": subject,
                "path": f"{subject}/{unit_file.name}",
                "unit": unit,
                "problems": unit_problems,
            })

    current, superseded = group_versions(records)
    for record in current:
        problems.extend(record["problems"])

    current_units = [r["unit"] for r in current if r["unit"]]
    superseded_units = [r["unit"] for r in superseded if r["unit"]]
    # A `[[slug]]` names the knowledge, not a revision, so it resolves against every version.
    known = {record["slug"] for record in records}
    problems.extend(dangling_references(current_units, known))
    return current_units, superseded_units, problems


def stamp_problem(subject: str) -> str:
    """Name the actual fix for a subject folder that fails the stamp check."""
    if STAMP_ONLY_RE.match(subject):
        return (
            f"{subject}/ has a stamp but no subject name in front of it — rename to "
            f"<subject>{subject}/ (kebab-case subject, then the -yyyyMMdd-HHmm stamp)"
        )
    malformed = MALFORMED_STAMP_RE.match(subject)
    if malformed:
        return (
            f"{subject}/ has a malformed creation stamp — the suffix must be exactly -yyyyMMdd-HHmm "
            f"(8 digits, dash, 4 digits; 24-hour UTC); rename to {malformed.group(1)}-<yyyyMMdd-HHmm>/"
        )
    return (
        f"{subject}/ is missing the <subject>-yyyyMMdd-HHmm creation stamp — rename to "
        f"{subject}-<yyyyMMdd-HHmm>/ (24-hour UTC; '{UNFILED}' is the only exempt folder)"
    )


def stamp_of(subject: str) -> str:
    """The `yyyyMMdd-HHmm` suffix of a subject folder, or '' when it has none.

    Fixed-width and zero-padded, so lexical order is chronological order. `_unfiled` and any
    folder failing the stamp check return '' and therefore sort oldest — `_unfiled` is a permanent
    catch-all rather than an export run, so a stamped improvement always supersedes a copy parked
    there.
    """
    return subject[-13:] if SUBJECT_STAMP_RE.match(subject) else ""


def version_key(record: dict) -> tuple[str, str, str]:
    """Recency of one copy of a slug. Folder stamp decides; `updated` and path break ties.

    The fallback matters for `_unfiled` and for two runs that landed in the same minute — the
    worktask's stated default is that the folder stamp decides, falling back to `updated`. Path
    is last so the result is deterministic rather than filesystem-order dependent.
    """
    fields = record["unit"] or {}
    return (stamp_of(record["subject"]), str(fields.get("updated") or ""), record["path"])


def group_versions(records: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split every copy of every slug into (current, superseded).

    One slug has exactly one current version: the copy with the highest `version_key`. This
    replaces the retired `duplicate_slugs` check — a repeated slug is the versioning mechanism
    now, and the cost of that is real: a typo'd slug colliding with unrelated knowledge is no
    longer distinguishable from a deliberate revision, and nothing mechanical catches it. The
    export procedure's reconcile step is what prevents it.
    """
    by_slug: dict[str, list[dict]] = {}
    for record in records:
        by_slug.setdefault(record["slug"], []).append(record)

    newest = {slug: max(copies, key=version_key) for slug, copies in by_slug.items()}
    current_paths = {record["path"] for record in newest.values()}
    current = [r for r in records if r["path"] in current_paths]
    superseded = [r for r in records if r["path"] not in current_paths]
    return current, superseded


def iter_reference_fields(unit: dict):
    """Yield every (field-path, list) in a unit's frontmatter that could hold `[[slug]]` refs.

    Walks the shape generically — top-level lists and lists one level inside a map — so a
    field added to the template is validated without touching this file. Parsing was already
    generic; validation used to be per-field, and a new field went silently unchecked.
    """
    for key, value in unit.items():
        if key in ("folder", "subject", "path"):
            continue
        if isinstance(value, list):
            yield key, value
        elif isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, list):
                    yield f"{key}.{sub_key}", sub_value


# How to word an unresolvable reference, per field. Any field not listed gets the default.
REFERENCE_REMEDIES = {
    "provenance.inherited": (
        "is no longer in the store — restore it, point at what superseded it, "
        "or unbracket it to keep the lineage"
    ),
}
DEFAULT_REMEDY = "has no matching Understanding"


def dangling_references(units: list[dict], known: set[str]) -> list[str]:
    """An unresolvable `[[slug]]` in any frontmatter list, wherever it appears.

    Only bracketed entries are references. A bare string is a historical note — that is how a
    lineage survives the Understanding it names being pruned or promoted away.

    `known` covers every version of every slug, including superseded copies: a link means the
    knowledge, so it resolves as long as some copy of that slug exists.
    """
    dangling = []
    for unit in units:
        for field, values in iter_reference_fields(unit):
            for entry in values:
                entry = str(entry).strip()
                if not entry.startswith("[[") or placeholder(entry):
                    continue
                target = entry.strip("[]")
                if target and target not in known:
                    remedy = REFERENCE_REMEDIES.get(field, DEFAULT_REMEDY)
                    dangling.append(f"{unit['path']}: {field} [[{target}]] {remedy}")
    return dangling


def inherited_targets(units: list[dict]) -> set[str]:
    """Every slug any unit records having acted on. The store's only usage signal.

    The list guard is load-bearing. A flow-style or bare scalar (`inherited: [[beta]]`) parses as a
    string, and iterating it yields characters: the real target is lost *and* the garbage entries make
    `lineage_recorded` true, so every unit reports as never inherited. A current unit carrying that
    shape is caught by `inline_sequences`, but a superseded copy is exempt from validation while still
    feeding this function — so without the guard an old copy corrupts the report with nothing printed
    and exit 0.
    """
    targets = set()
    for unit in units:
        provenance = unit.get("provenance")
        if not isinstance(provenance, dict):
            continue
        inherited = provenance.get("inherited")
        if not isinstance(inherited, list):
            continue
        for entry in inherited:
            targets.add(str(entry).strip().strip("[]"))
    return targets


def days_since(value) -> int | None:
    try:
        return (date.today() - date.fromisoformat(str(value).strip())).days
    except ValueError:
        return None


def review(units: list[dict], superseded: list[dict] | None = None) -> list[str]:
    """Advisory decay report: which units are worth re-reading, pruning or promoting.

    Not validation — none of this is wrong, and the report never changes the exit code. It exists
    because a store that only grows stops being readable, and nothing else notices.

    Runs over current versions only, and the never-inherited signal counts inheritance of **any**
    version: usage accrues to the slug, so a unit improved three times is not reported as unused
    because the lineage names an earlier revision.
    """
    superseded = superseded or []
    used = inherited_targets(units + superseded)
    # In a store where nothing has recorded inheritance yet, "never inherited" carries no signal.
    lineage_recorded = bool(used)

    lines = []
    for unit in units:
        flags = []
        is_outcome = not unit.get("question")
        age = days_since(unit.get("updated"))
        limit = STALE_AFTER_DAYS_OUTCOME if is_outcome else STALE_AFTER_DAYS

        if unit.get("confidence") == "contested":
            flags.append("contested — the code disagreed with it; confirm or retire")
        if lineage_recorded and unit["folder"] not in used:
            flags.append("never inherited — the question may not match what anyone actually asks")
        if age is not None and age > limit:
            kind = "outcome" if is_outcome else "knowledge"
            flags.append(f"{age}d since update ({kind} unit, flagged past {limit}d) — re-check it still holds")
        if flags:
            lines.append(f"{unit['path']}:")
            lines.extend(f"    {f}" for f in flags)

    revisions: dict[str, int] = {}
    for unit in superseded:
        revisions[unit["folder"]] = revisions.get(unit["folder"], 0) + 1
    for slug in sorted(revisions):
        lines.append(
            f"{slug}: {revisions[slug]} superseded copy(ies) on disk — prune guidance only; "
            f"history is never deleted automatically"
        )
    return lines


def cell(value) -> str:
    if not isinstance(value, str) or not value:
        return "—"
    return value.replace("|", "\\|")


def render(units: list[dict]) -> str:
    lines = [
        "# Understandings — INDEX",
        "",
        "Generated by `.agents/skills/ai-understanding/scripts/understanding_index.py`. Do not hand-edit.",
        "",
        "Grouped by subject for browsing; every Understanding is listed individually because knowledge is",
        "retrieved by the **question** it answers, not by the subject that produced it. Match a question",
        "against what you are about to ask, then read only the units that matched.",
        "",
        "One row per slug, resolving to its **newest** version. A slug repeated across stamped folders is a",
        "version chain; superseded copies stay on disk, unlisted. When two Understandings conflict, the newer",
        "wins — but the system outranks both.",
        "",
    ]

    if not units:
        lines += ["_No Understandings encoded yet._", ""]
        return "\n".join(lines)

    subjects: dict[str, list[dict]] = {}
    for unit in units:
        subjects.setdefault(unit["subject"], []).append(unit)

    for subject in sorted(subjects):
        lines += [
            f"## {subject}",
            "",
            "| Understanding | Description | Question | Scope | Confidence | Updated |",
            "|---------------|-------------|----------|-------|------------|---------|",
        ]
        for unit in subjects[subject]:
            path = unit["path"]
            lines.append(
                f"| [`{unit['folder']}`](./{path}) | {cell(unit.get('description'))} "
                f"| {cell(unit.get('question'))} | {cell(unit.get('scope'))} "
                f"| {cell(unit.get('confidence'))} | {cell(unit.get('updated'))} |"
            )
        lines.append("")
    return "\n".join(lines)


USAGE = f"""usage: understanding_index.py [store-dir] [--review]

Regenerate INDEX.md from the <subject>-<yyyyMMdd-HHmm>/<slug>.md units.
A slug repeated across stamped folders is a version chain: the newest stamp is indexed,
older copies stay on disk unlisted and exempt from validation.
Defaults to {DEFAULT_STORE}. --review adds an advisory decay report.

Exit codes: 0 clean · 1 validation problems (index still written) · 2 store not found."""


def main(argv: list[str]) -> int:
    args = argv[1:]
    if any(a in ("-h", "--help") for a in args):
        print(USAGE)
        return 0
    wants_review = "--review" in args
    args = [a for a in args if a != "--review"]
    unknown = [a for a in args if a.startswith("-")]
    if unknown:
        print(f"unknown option: {unknown[0]}\n\n{USAGE}", file=sys.stderr)
        return 2
    if len(args) > 1:
        print(f"expected at most one store-dir, got {len(args)}\n\n{USAGE}", file=sys.stderr)
        return 2

    store = Path(args[0]) if args else DEFAULT_STORE
    if not store.is_dir():
        print(f"store not found: {store}", file=sys.stderr)
        return 2

    units, superseded, problems = load_units(store)
    (store / "INDEX.md").write_text(render(units), encoding="utf-8")
    subject_count = len({unit["subject"] for unit in units})
    history = f", {len(superseded)} superseded copy(ies) unlisted" if superseded else ""
    print(
        f"indexed {len(units)} understanding(s) across {subject_count} subject(s){history} "
        f"-> {store / 'INDEX.md'}"
    )

    if wants_review:
        report = review(units, superseded)
        print("\nreview — advisory, does not affect the exit code")
        print("\n".join(report) if report else "    nothing flagged")

    for problem in problems:
        print(f"  problem: {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
