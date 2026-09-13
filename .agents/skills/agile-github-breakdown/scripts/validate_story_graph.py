#!/usr/bin/env python3
"""
Skill: agile-github-breakdown
Validate a drafted Task dependency graph and check FR/NFR coverage.

Input JSON (file argument or stdin):
{
  "requirement_ids": ["FR-1", "NFR-11", ...],        // optional; from parse_frnfr.py
  "stories": [
    {"key": "S1", "depends_on": [], "ac_ids": ["NFR-11"]},
    {"key": "S2", "depends_on": ["S1"], "ac_ids": ["FR-1"]}
  ]
}

A depends_on entry that is not another story's "key" in this same input (e.g. an
already-existing GitHub issue like "#42") is treated as external and skipped for
cycle detection. Pass --known-external to avoid it being flagged as dangling.

Output JSON report on stdout:
{
  "duplicate_story_keys": ["S1"],           // non-empty -> hard error, exit 1. A later story
                                             // with a repeated key would otherwise silently
                                             // replace an earlier one, hiding cycles/edges the
                                             // earlier definition carried.
  "cycles": [["S1", "S2", "S1"]],           // non-empty -> hard error, exit 1
  "dangling_depends_on": [["S3", "S9"]],    // S3 depends on S9; S9 is neither a story key
                                             // nor in --known-external -> hard error, exit 1
  "missing_coverage": ["NFR-9"],            // requirement_ids not cited by any story's ac_ids -> warning
  "unknown_ac_ids": ["FR-99"],              // an ac_ids entry that cites no requirement_ids member ->
                                             // hard error, exit 1. Only checked when the input actually
                                             // supplied "requirement_ids" -- omitting that key entirely
                                             // (e.g. validating a graph with no coverage data at all)
                                             // must not flag every ac_ids entry as unknown.
  "subnumber_suggestions": [["S3", "S4"]]   // S3 is the sole thing S4 depends on, and S4 depends
                                             // on nothing else -> stub/consumer candidate for N.1/N.2
}
Exit code: 1 if duplicate_story_keys, cycles, dangling_depends_on, or unknown_ac_ids is non-empty,
else 0. Coverage gaps and sub-numbering suggestions are warnings only; they never fail the run.
Exit code 2 means the input itself was malformed (not a JSON object, a missing or non-list
"stories" member, or a story entry without a "key") — a different class from a graph that parsed
but failed validation. "stories" must be present; `[]` is accepted, absence is not.
"""
import argparse
import json
import sys


def list_of_strings_problem(value, label):
    """Return a problem description if value isn't a list of strings, else None.

    A bare string passes `set(...)` and `.update(...)` happily but iterates *characters*,
    so `"FR-12"` and `"FR-21"` compare as equal character sets and coverage diffs come back
    empty — an all-clear on malformed input. Same trap for depends_on, where a string
    dependency becomes one dangling entry per character.
    """
    if not isinstance(value, list):
        return f"{label} must be a list of strings, got {type(value).__name__}"
    for i, item in enumerate(value):
        if not isinstance(item, str):
            return f"{label}[{i}] must be a string, got {type(item).__name__}"
    return None


def check_input(data):
    """Return a list of human-readable problems with the input's shape, empty if it's usable.

    Checked up front so a malformed entry names itself instead of surfacing as a KeyError
    traceback from deep in the report build — this input is agent-authored, so an omitted
    "key" is a realistic mistake and the message is what tells the agent to fix its own draft.
    """
    if not isinstance(data, dict):
        return [f"top level must be a JSON object, got {type(data).__name__}"]

    # "stories" is required, not defaulted. An accidental omission (typo, or the key
    # named "story") would otherwise read as an empty graph and report all-clear on a
    # payload carrying no draft at all. An explicitly empty list stays valid: paired
    # with "requirement_ids" it answers "nothing drafted yet, what is uncovered?".
    # "requirement_ids" is deliberately optional by contract -- omitting it disables
    # the unknown_ac_ids check -- so do not make it required here.
    if "stories" not in data:
        return ['top level is missing the required "stories" member']

    stories = data["stories"]
    if not isinstance(stories, list):
        return [f'"stories" must be a list, got {type(stories).__name__}']

    problems = []

    if "requirement_ids" in data:
        problem = list_of_strings_problem(data["requirement_ids"], '"requirement_ids"')
        if problem:
            problems.append(problem)

    for i, story in enumerate(stories):
        if not isinstance(story, dict):
            problems.append(f"stories[{i}] must be an object, got {type(story).__name__}")
            continue
        if not story.get("key"):
            problems.append(f'stories[{i}] is missing a non-empty "key"')
        elif not isinstance(story["key"], str):
            problems.append(
                f'stories[{i}]["key"] must be a string, got {type(story["key"]).__name__}'
            )
        for field in ("depends_on", "ac_ids"):
            if field in story:
                problem = list_of_strings_problem(story[field], f'stories[{i}]["{field}"]')
                if problem:
                    problems.append(problem)

    return problems


def find_cycles(stories_by_key):
    cycles = []
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {k: WHITE for k in stories_by_key}

    def dfs(key, path):
        color[key] = GRAY
        path.append(key)
        for dep in stories_by_key[key]["depends_on"]:
            if dep not in stories_by_key:
                continue  # external reference, not a cycle candidate here
            if color[dep] == GRAY:
                idx = path.index(dep)
                cycles.append(path[idx:] + [dep])
            elif color[dep] == WHITE:
                dfs(dep, path)
        path.pop()
        color[key] = BLACK

    for key in stories_by_key:
        if color[key] == WHITE:
            dfs(key, [])
    return cycles


def build_report(data, known_external):
    stories = data.get("stories", [])
    requirement_ids = set(data.get("requirement_ids", []))

    story_keys = [s["key"] for s in stories]
    duplicate_story_keys = sorted({k for k in story_keys if story_keys.count(k) > 1})

    # A dict comprehension keeps only the LAST of a duplicate key, which would silently
    # drop an earlier story's depends_on/ac_ids and hide a cycle it was part of. Duplicates
    # are reported as a hard error above; still build this so the rest of the report is
    # well-formed JSON rather than raising past that error.
    stories_by_key = {
        s["key"]: {"depends_on": s.get("depends_on", []), "ac_ids": s.get("ac_ids", [])}
        for s in stories
    }

    dangling = []
    for s in stories:
        for dep in s.get("depends_on", []):
            if dep not in stories_by_key and dep not in known_external:
                dangling.append([s["key"], dep])

    cycles = find_cycles(stories_by_key)

    cited = set()
    for s in stories:
        cited.update(s.get("ac_ids", []))
    missing_coverage = sorted(requirement_ids - cited)

    # cited - requirement_ids catches an ac_ids entry that cites no real requirement --
    # an invented or mistyped ID. Only meaningful when the caller actually supplied
    # requirement_ids; if that key is absent entirely (no coverage data at all), every
    # ac_ids entry would otherwise be flagged as unknown, which is a false positive.
    unknown_ac_ids = sorted(cited - requirement_ids) if "requirement_ids" in data else []

    # Who (within this story set) depends on each key
    dependents = {k: [] for k in stories_by_key}
    for s in stories:
        for dep in s.get("depends_on", []):
            if dep in dependents:
                dependents[dep].append(s["key"])

    subnumber_suggestions = []
    for key, deps in dependents.items():
        if len(deps) == 1:
            consumer = deps[0]
            if stories_by_key[consumer]["depends_on"] == [key]:
                subnumber_suggestions.append([key, consumer])

    return {
        "duplicate_story_keys": duplicate_story_keys,
        "cycles": cycles,
        "dangling_depends_on": dangling,
        "missing_coverage": missing_coverage,
        "unknown_ac_ids": unknown_ac_ids,
        "subnumber_suggestions": subnumber_suggestions,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file", nargs="?", help="JSON file to validate; omit to read stdin")
    ap.add_argument(
        "--known-external",
        nargs="*",
        default=[],
        help="Existing GitHub issue refs (e.g. #42) depends_on may cite without being flagged dangling",
    )
    args = ap.parse_args()

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            raw = f.read()
    else:
        raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"ERROR: input is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(2)

    problems = check_input(data)
    if problems:
        print("ERROR: malformed input:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        sys.exit(2)

    report = build_report(data, set(args.known_external))
    print(json.dumps(report, indent=2))

    if (
        report["duplicate_story_keys"]
        or report["cycles"]
        or report["dangling_depends_on"]
        or report["unknown_ac_ids"]
    ):
        sys.exit(1)


if __name__ == "__main__":
    main()
