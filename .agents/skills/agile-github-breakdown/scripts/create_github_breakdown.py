#!/usr/bin/env python3
"""Create a GitHub Feature + Task breakdown from a drafted JSON graph.

The agent authors titles/bodies/AC. This script owns gh argv (shell=False): create
Feature (optional), create Tasks, add them to the Project, link Tasks as sub-issues,
and set blocked_by dependencies.

Vanilla GitHub issue types only — Feature and Task. Never create an issue type.
"""

import argparse
import json
import subprocess
import sys


TRANSLATION_HEADING = "## Translation (AI context)"
TRANSLATION_TABLE_MARKER = "| Role | GitHub |"

TRANSLATION_TABLE = """\
## Translation (AI context)

Vanilla GitHub Projects graph used by this skill. Keep this table in the issue so
later agents (and humans) map Jira-shaped language onto GitHub without inventing
an Epic type.

| Role | GitHub | Notes |
|------|--------|-------|
| Initiative | **Project** | Existing GitHub Project. Do not create a Project. |
| Epic | **Feature** issue (`--type Feature`) | Top-level. No parent unless the user gives one. |
| Story | **Task** issue (`--type Task`) | Sub-issue of the Feature. FR/NFR → acceptance criteria. |
| Subtask | Untyped issue (no `--type`) | Out of scope here. `agile-github-task-from-diff` later. |

Do not create org issue types. Stock types are Task / Bug / Feature only.
"""


def run(cmd, check=True, capture=True):
    # cmd is always a list (shell=False), so argv is passed directly to the OS with
    # no shell interpretation — git/gh args cannot be shell-injected even if a value
    # contains spaces or metacharacters. Never pass a string or add shell=True here.
    result = subprocess.run(cmd, check=check, text=True, capture_output=capture)
    return result.stdout.strip()


def run_json(cmd):
    result = subprocess.run(cmd, check=True, text=True, capture_output=True)
    return json.loads(result.stdout)


def ensure_tool(name):
    try:
        run([name, "--version"], check=True)
    except Exception:
        raise RuntimeError(f"Required tool not available: {name}")


def get_repo_info():
    """Detect owner/repo from the git remote URL."""
    remote = run(["git", "remote", "get-url", "origin"])
    if "github.com" not in remote:
        raise RuntimeError("Remote origin does not appear to be a GitHub repository.")
    remote = remote.replace("git@github.com:", "https://github.com/").rstrip("/").removesuffix(".git")
    parts = remote.split("github.com/")[-1].split("/")
    if len(parts) >= 2:
        return parts[0], parts[1]
    raise RuntimeError(f"Could not parse owner/repo from remote URL: {remote}")


def parse_issue_ref(value):
    """Accept an issue number, '#42', or a GitHub issue URL and return the int."""
    if value is None or value == "":
        return 0
    value = str(value).strip()
    if value.startswith("http"):
        parts = value.rstrip("/").split("/")
        try:
            return int(parts[-1])
        except (ValueError, IndexError):
            raise RuntimeError(f"Could not parse issue number from URL: {value}")
    if value.startswith("#"):
        value = value[1:]
    try:
        return int(value)
    except ValueError:
        raise RuntimeError(f"Issue ref must be an integer, #N, or GitHub issue URL, got: {value}")


def ensure_translation_table(body):
    """Append the translation table unless the table itself is already present."""
    body = (body or "").rstrip()
    if TRANSLATION_TABLE_MARKER in body:
        return body + "\n"
    if TRANSLATION_HEADING in body:
        after_heading = TRANSLATION_TABLE.split(TRANSLATION_HEADING, 1)[-1].lstrip("\n")
        return body + "\n\n" + after_heading
    if body:
        return body + "\n\n" + TRANSLATION_TABLE
    return TRANSLATION_TABLE


def md_cell(value):
    """Flatten whitespace and escape pipes so a title cannot split a table row."""
    return " ".join(str(value).split()).replace("|", r"\|")


def build_tasks_table(created):
    """Markdown table mapping draft keys to created issue numbers."""
    lines = [
        "## Tasks",
        "",
        "| Key | Issue | Title |",
        "|-----|-------|-------|",
    ]
    for item in created:
        lines.append(
            f"| {md_cell(item['key'])} | #{item['number']} | {md_cell(item['title'])} |"
        )
    return "\n".join(lines) + "\n"


def parse_tasks_table(body):
    """Return existing Tasks-table rows from a Feature body, or []."""
    rows = []
    in_table = False
    for line in (body or "").splitlines():
        if line.startswith("## Tasks"):
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if not in_table or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        if cells[0].lower() == "key" or set(cells[0]) <= {"-", ":"}:
            continue
        try:
            number = int(cells[1].lstrip("#"))
        except ValueError:
            continue
        rows.append({"key": cells[0], "number": number, "title": cells[2]})
    return rows


def merge_created(existing, created):
    """Keep prior key→issue rows; current-batch rows win on the same key."""
    by_key = {row["key"]: row for row in existing}
    order = [row["key"] for row in existing]
    for row in created:
        by_key[row["key"]] = row
        if row["key"] not in order:
            order.append(row["key"])
    return [by_key[key] for key in order]


def _rest_after_tasks_section(remainder):
    if remainder.startswith("## "):
        return remainder
    found = remainder.find("\n## ")
    if found == -1:
        return ""
    return remainder[found + 1 :]


def ensure_tasks_table(body, created):
    """Replace or append the Tasks table so keys stay mapped to issue numbers."""
    table = build_tasks_table(created)
    body = (body or "").rstrip() + "\n"
    marker = "## Tasks\n"
    if marker not in body:
        return body + "\n" + table
    before, _, rest = body.partition(marker)
    remainder = rest.lstrip("\n")
    after = _rest_after_tasks_section(remainder)
    return before + table + ("\n" + after if after else "")


def issue_number_from_url(url):
    return int(url.rstrip("/").split("/")[-1])


def create_issue(owner, repo, title, body, issue_type):
    url = run([
        "gh", "issue", "create",
        "--repo", f"{owner}/{repo}",
        "--title", title,
        "--body", body,
        "--type", issue_type,
    ])
    return issue_number_from_url(url), url


def fetch_issue(owner, repo, number):
    return run_json(["gh", "api", f"/repos/{owner}/{repo}/issues/{number}"])


def add_to_project(org, project, issue_url):
    run([
        "gh", "project", "item-add", str(project),
        "--owner", org,
        "--url", issue_url,
    ])


def link_sub_issue(owner, repo, parent_number, child_id):
    """Link child (database id) as a sub-issue of parent. Soft-fail."""
    try:
        run_json([
            "gh", "api", "--method", "POST",
            f"/repos/{owner}/{repo}/issues/{parent_number}/sub_issues",
            "-f", f"sub_issue_id={child_id}",
        ])
        return True
    except Exception:
        return False


def add_blocked_by(owner, repo, blocked_number, blocker_id):
    """Mark blocked_number as blocked by blocker_id (database id). Soft-fail."""
    try:
        # 201 may have an empty body; do not json-parse stdout. -F types issue_id as int.
        run([
            "gh", "api", "--method", "POST",
            f"/repos/{owner}/{repo}/issues/{blocked_number}/dependencies/blocked_by",
            "-F", f"issue_id={blocker_id}",
        ])
        return True
    except Exception:
        return False


def patch_issue_body(owner, repo, number, body):
    payload = json.dumps({"body": body})
    result = subprocess.run(
        [
            "gh", "api", "--method", "PATCH",
            f"/repos/{owner}/{repo}/issues/{number}",
            "--input", "-",
        ],
        input=payload,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def load_payload(path):
    if path:
        with open(path, encoding="utf-8") as handle:
            raw = handle.read()
    else:
        raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Payload is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Payload must be a JSON object.")
    if "tasks" not in data or not isinstance(data["tasks"], list):
        raise RuntimeError('Payload is missing a "tasks" list.')
    if "feature" not in data or not isinstance(data["feature"], dict):
        raise RuntimeError('Payload is missing a "feature" object.')
    return data


def resolve_dep(dep, key_to_number):
    """Map a draft key or #N ref to an issue number."""
    if dep in key_to_number:
        return key_to_number[dep]
    return parse_issue_ref(dep)


def validate_tasks(tasks):
    """Reject malformed tasks before any GitHub write."""
    seen = set()
    for i, task in enumerate(tasks):
        if not isinstance(task, dict) or not task.get("key"):
            raise RuntimeError(f"tasks[{i}] is missing a non-empty \"key\".")
        if not isinstance(task["key"], str):
            raise RuntimeError(f"tasks[{i}][\"key\"] must be a string.")
        if not task.get("title"):
            raise RuntimeError(f"tasks[{i}] ({task['key']}) is missing a title.")
        if task["key"] in seen:
            raise RuntimeError(f"duplicate task key {task['key']!r}.")
        seen.add(task["key"])
        deps = task.get("depends_on")
        if deps is None:
            continue
        if not isinstance(deps, list) or any(not isinstance(dep, str) for dep in deps):
            raise RuntimeError(
                f"tasks[{i}] ({task['key']}) depends_on must be a list of strings."
            )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Create a GitHub Feature + Task breakdown from a drafted JSON graph, "
            "add issues to the GitHub Project, link Tasks as sub-issues, and set blocked_by."
        )
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="JSON payload path; omit to read stdin.",
    )
    parser.add_argument(
        "--feature-issue",
        help=(
            "Existing Feature issue — number, #N, or URL. When set, skip Feature "
            "creation and attach Tasks under this issue."
        ),
    )
    parser.add_argument(
        "--repo",
        help="GitHub repo as owner/repo. Auto-detected from git remote when omitted.",
    )
    parser.add_argument(
        "--project",
        type=int,
        default=1,
        help="GitHub project number under the org (default: 1).",
    )
    parser.add_argument(
        "--no-project",
        action="store_true",
        help="Create the issues only; do not add them to any GitHub Project.",
    )
    parser.add_argument(
        "--org",
        help="GitHub org that owns the project. Defaults to the repo owner.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write to GitHub. Default is dry-run preview.",
    )

    args = parser.parse_args()

    ensure_tool("git")
    ensure_tool("gh")

    if args.repo:
        owner, repo = args.repo.split("/", 1)
    else:
        owner, repo = get_repo_info()
    org = args.org or owner

    data = load_payload(args.file)
    feature = data["feature"]
    tasks = data["tasks"]

    feature_title = feature.get("title") or "(untitled Feature)"
    feature_body = ensure_translation_table(feature.get("body") or "")
    feature_number = parse_issue_ref(args.feature_issue) or parse_issue_ref(feature.get("number"))

    validate_tasks(tasks)

    if not args.apply:
        print(f"Repo: {owner}/{repo}")
        if args.no_project:
            print("Project: skipped (--no-project)")
        else:
            print(f"Project: {org}/projects/{args.project}")
        if feature_number:
            print(f"Feature: reuse #{feature_number} — {feature_title}")
        else:
            print(f"Feature: CREATE --type Feature — {feature_title}")
        print()
        print("Feature body:")
        print(feature_body)
        print()
        print("Tasks:")
        for task in tasks:
            deps = task.get("depends_on") or []
            dep_note = f" blocked by {', '.join(deps)}" if deps else " (unblocked)"
            print(f"  {task['key']}: CREATE --type Task — {task['title']}{dep_note}")
            print()
            print(ensure_translation_table(task.get("body") or ""))
            print()
        print("Dry run. Re-run with --apply after explicit go-ahead.")
        return 0

    created = []

    if feature_number:
        feature_issue = fetch_issue(owner, repo, feature_number)
        feature_url = feature_issue["html_url"]
        print(f"Reusing Feature #{feature_number}: {feature_url}")
        if not args.no_project:
            try:
                add_to_project(org, args.project, feature_url)
                print(f"Added Feature #{feature_number} to project {org}/projects/{args.project}.")
            except Exception as exc:
                print(f"Warning: could not add Feature to project: {exc}", file=sys.stderr)
    else:
        feature_number, feature_url = create_issue(
            owner, repo, feature_title, feature_body, "Feature",
        )
        print(f"Created Feature #{feature_number}: {feature_url}")
        if not args.no_project:
            try:
                add_to_project(org, args.project, feature_url)
                print(f"Added Feature #{feature_number} to project {org}/projects/{args.project}.")
            except Exception as exc:
                print(f"Warning: could not add Feature to project: {exc}", file=sys.stderr)

    key_to_number = {}
    key_to_id = {}
    for task in tasks:
        body = ensure_translation_table(task.get("body") or "")
        number, url = create_issue(owner, repo, task["title"], body, "Task")
        issue = fetch_issue(owner, repo, number)
        key_to_number[task["key"]] = number
        key_to_id[task["key"]] = issue["id"]
        created.append({"key": task["key"], "number": number, "title": task["title"], "url": url})
        print(f"Created Task {task['key']} #{number}: {url}")
        if not args.no_project:
            try:
                add_to_project(org, args.project, url)
            except Exception as exc:
                print(f"Warning: could not add Task #{number} to project: {exc}", file=sys.stderr)
        if not link_sub_issue(owner, repo, feature_number, issue["id"]):
            print(
                f"Note: sub-issue API link failed. "
                f"Manually add #{number} as a sub-issue of #{feature_number}.",
                file=sys.stderr,
            )

    for task in tasks:
        blocked_number = key_to_number[task["key"]]
        for dep in task.get("depends_on") or []:
            try:
                if dep in key_to_id:
                    blocker_id = key_to_id[dep]
                    blocker_number = key_to_number[dep]
                else:
                    blocker_number = resolve_dep(dep, key_to_number)
                    blocker_id = fetch_issue(owner, repo, blocker_number)["id"]
            except Exception as exc:
                print(
                    f"Note: could not resolve blocker {dep!r} for {task['key']}: {exc}",
                    file=sys.stderr,
                )
                continue
            if not add_blocked_by(owner, repo, blocked_number, blocker_id):
                print(
                    f"Note: blocked_by link failed. "
                    f"Manually mark #{blocked_number} blocked by #{blocker_number}.",
                    file=sys.stderr,
                )

    # Keep the Feature body mapped to created Task numbers for later agents.
    try:
        current = fetch_issue(owner, repo, feature_number)
        current_body = current.get("body") or feature_body
        updated = ensure_translation_table(current_body)
        updated = ensure_tasks_table(updated, merge_created(parse_tasks_table(current_body), created))
        patch_issue_body(owner, repo, feature_number, updated)
        print(f"Updated Feature #{feature_number} Tasks table.")
    except Exception as exc:
        print(f"Warning: could not patch Feature body: {exc}", file=sys.stderr)

    print()
    print(f"Feature #{feature_number}: {feature_url}")
    for item in created:
        print(f"  {item['key']} -> #{item['number']} {item['url']}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
