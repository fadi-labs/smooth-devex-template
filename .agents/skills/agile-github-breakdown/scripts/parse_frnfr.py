#!/usr/bin/env python3
"""
Skill: agile-github-breakdown
Normalise an explicitly delimited requirement list into JSON.

The agent extracts the FR/NFR rows out of the Feature body — it already holds that body in
context — and passes them here **one requirement per line**:

    FR-1 | The system must accept a line recipe payload
    NFR-11 | p95 < 5s for a single recipe read

This script does the deterministic, token-expensive-by-hand work: strict validation with
line numbers, prefix filtering, duplicate detection, numeric-aware sorting, and JSON for
`validate_story_graph.py`. It does **not** parse Markdown.

That is deliberate. An earlier version discovered requirement tables inside an arbitrary
Markdown document, and every review round found another way for that discovery to go wrong
while still exiting 0 — optional outer pipes making prose indistinguishable from a row, a
fenced example claiming the real IDs, block quotes and list items consumed as rows, ragged
rows terminating the scan, indentation and fence-closing rules. The input surface was the
whole CommonMark/GFM spec. Narrowing the contract deletes the entire class: there is no
"find the table" step left to get wrong.

Contract:
  * One requirement per line, `<ID> | <text>`. The ID is `[A-Z]{2,6}-<digits>`, bare — no
    bold, link or code wrappers, because the caller is writing this line, not quoting a
    document.
  * The text is everything after the first `|`, so it may itself contain pipes.
  * Blank lines are ignored. Any other non-conforming line is a hard error naming the line
    number — never a silent skip, since a dropped requirement is invisible downstream.

Exit codes:
  0  requirements parsed
  1  zero requirements matched (a coverage gate that passes on an empty list is worthless)
  2  malformed input

Usage:
  parse_frnfr.py ids.txt
  printf 'FR-1 | text\\nNFR-2 | other\\n' | parse_frnfr.py --prefix FR NFR
"""
import argparse
import json
import re
import sys

ID_RE = re.compile(r"^[A-Z]{2,6}-\d+$")


def parse(text, prefixes=None):
    """Return (requirements, duplicate_ids, problems) for an explicit requirement list."""
    seen = {}
    duplicates = []
    problems = []

    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue

        if "|" not in stripped:
            problems.append(f"line {number}: expected '<ID> | <text>', found {stripped!r}")
            continue

        raw_id, _, raw_text = stripped.partition("|")
        req_id = raw_id.strip()
        req_text = raw_text.strip()

        if not ID_RE.match(req_id):
            problems.append(
                f"line {number}: {req_id!r} is not a bare requirement ID "
                "(expected e.g. FR-1, NFR-11)"
            )
            continue
        if not req_text:
            problems.append(f"line {number}: {req_id} has no requirement text")
            continue

        if prefixes and not any(req_id.startswith(p + "-") for p in prefixes):
            continue  # deliberately filtered, not malformed

        if req_id in seen:
            duplicates.append(req_id)
            continue
        seen[req_id] = req_text

    return seen, duplicates, problems


def sort_key(item):
    prefix, number = item[0].rsplit("-", 1)
    return (prefix, int(number))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file", nargs="?", help="Requirement list to read; omit to read stdin")
    # nargs="+" not "*": a bare `--prefix` would yield [], which is falsy and would silently
    # disable both the filter and the zero-match hard stop below.
    ap.add_argument("--prefix", nargs="+", help="Restrict to these ID prefixes, e.g. FR NFR")
    args = ap.parse_args()

    if args.file:
        with open(args.file, encoding="utf-8") as handle:
            text = handle.read()
    else:
        text = sys.stdin.read()

    requirements, duplicates, problems = parse(text, args.prefix)

    if problems:
        print("ERROR: malformed requirement list:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        sys.exit(2)

    result = [{"id": k, "text": v} for k, v in sorted(requirements.items(), key=sort_key)]
    print(json.dumps({"requirements": result, "duplicate_ids": sorted(set(duplicates))}, indent=2))

    if duplicates:
        print(f"WARNING: duplicate IDs in source: {sorted(set(duplicates))}", file=sys.stderr)

    if not result:
        scope = f" matching prefixes {args.prefix}" if args.prefix else ""
        print(
            f"ERROR: no requirements{scope} found. An empty list would pass every "
            "downstream coverage check while omitting every requirement.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
