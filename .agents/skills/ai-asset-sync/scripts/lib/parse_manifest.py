#!/usr/bin/env python3
"""Parse the constrained ai-sync manifest / lockfile YAML subset.

Stdlib only. Accepts the schema in AGENTS.md — not general YAML.
"""
from __future__ import annotations

import re
import sys
from typing import Any

# Strict charsets: these values flow into `gh api repos/<owner>/<repo>/commits/<ref>`
# and `gh repo clone`, so URL metacharacters / option-looking values are rejected here.
SOURCE_RE = re.compile(
    r"^([A-Za-z0-9][A-Za-z0-9-]*)/([A-Za-z0-9_.][A-Za-z0-9._-]*)@([^:]+):(.+)$"
)
REF_RE = re.compile(r"^[A-Za-z0-9._/-]+$")

ALLOWED_STRATEGIES = ("ai-merge", "overwrite")


class ManifestError(ValueError):
    pass


def parse_source(source: str) -> dict[str, str]:
    """Split `owner/repo@ref:path` into fields. First ':' after '@' starts path."""
    raw = (source or "").strip()
    if not raw:
        raise ManifestError("empty source")
    m = SOURCE_RE.match(raw)
    if not m:
        raise ManifestError(
            f"invalid source '{source}': expected owner/repo@ref:path "
            "(owner/repo limited to [A-Za-z0-9._-], no leading '-')"
        )
    owner, repo, ref, path = m.group(1), m.group(2), m.group(3), m.group(4)
    if not owner or not repo or not ref or not path:
        raise ManifestError(f"invalid source '{source}': empty field")
    if (
        not REF_RE.match(ref)
        or ref.startswith(("-", "/"))
        or ".." in ref.split("/")
    ):
        raise ManifestError(f"unsafe ref in source '{source}'")
    if path.startswith(("/", "~", "-")) or ".." in path.split("/"):
        raise ManifestError(f"unsafe path in source '{source}'")
    segments = path.split("/")
    # Dangerous destinations: repo root itself, git control files, executable CI.
    if path in {".", "./"} or "" in segments or "." in segments:
        raise ManifestError(f"unsafe path in source '{source}'")
    if ".git" in segments:
        raise ManifestError(f"unsafe path in source '{source}': .git is not syncable")
    if path == ".github/workflows" or path.startswith(".github/workflows/"):
        raise ManifestError(
            f"unsafe path in source '{source}': workflow files are executable CI and are not syncable"
        )
    return {
        "owner": owner,
        "repo": repo,
        "ref": ref,
        "path": path,
        "source": f"{owner}/{repo}@{ref}:{path}",
    }


def _strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    out = []
    for ch in line:
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            break
        out.append(ch)
    return "".join(out).rstrip()


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    return value


def parse_manifest(text: str) -> dict[str, Any]:
    """Parse `.github/assets/ai-sync.yml` subset.

    version: 1
    entries:
      - source: owner/repo@ref:path
        strategy: ai-merge
    """
    entries: list[dict[str, str]] = []
    version = 1
    current: dict[str, str] | None = None
    in_entries = False
    entries_empty = False

    for lineno, raw in enumerate(text.splitlines(), 1):
        line = _strip_comment(raw)
        if not line.strip():
            continue
        stripped = line.strip()
        if stripped == "entries: []":
            in_entries = True
            entries_empty = True
            continue
        if re.match(r"^version:\s*", stripped):
            value = _unquote(stripped.split(":", 1)[1])
            try:
                version = int(value)
            except ValueError as exc:
                raise ManifestError(f"line {lineno}: version must be an int") from exc
            continue
        if stripped == "entries:":
            in_entries = True
            continue
        if not in_entries:
            raise ManifestError(f"line {lineno}: unexpected key '{stripped}'")
        if stripped.startswith("- "):
            if current:
                entries.append(_finalize_entry(current, lineno))
            current = {}
            rest = stripped[2:].strip()
            if rest:
                key, _, value = rest.partition(":")
                current[key.strip()] = _unquote(value)
            continue
        if current is None:
            raise ManifestError(f"line {lineno}: entry field without an item")
        if ":" not in stripped:
            raise ManifestError(f"line {lineno}: expected key: value")
        key, _, value = stripped.partition(":")
        current[key.strip()] = _unquote(value)

    if current:
        entries.append(_finalize_entry(current, lineno=0))
    if not in_entries and not entries_empty:
        raise ManifestError("manifest missing 'entries:'")
    if version != 1:
        raise ManifestError(f"unsupported manifest version {version}")
    seen = set()
    for entry in entries:
        src = entry["source"]
        if src in seen:
            raise ManifestError(f"duplicate source '{src}'")
        seen.add(src)
    # Overlapping local paths break cross-entry staging containment: an applied
    # parent would stage a blocked child's changes.
    paths = [e["path"].rstrip("/") for e in entries]
    for i, a in enumerate(paths):
        for b in paths[i + 1 :]:
            if a == b or a.startswith(b + "/") or b.startswith(a + "/"):
                raise ManifestError(f"overlapping entry paths '{a}' and '{b}'")
    return {"version": version, "entries": entries}


def _finalize_entry(current: dict[str, str], lineno: int) -> dict[str, str]:
    source = current.get("source")
    if not source:
        where = f"line {lineno}" if lineno else "entry"
        raise ManifestError(f"{where}: missing source")
    parsed = parse_source(source)
    strategy = current.get("strategy") or "ai-merge"
    if strategy not in ALLOWED_STRATEGIES:
        raise ManifestError(
            f"invalid strategy '{strategy}' (expected ai-merge|overwrite)"
        )
    parsed["strategy"] = strategy
    return parsed


def parse_lockfile(text: str) -> dict[str, Any]:
    """Parse `.github/assets/ai-sync.lock` subset. Empty/missing → no entries."""
    if not (text or "").strip():
        return {"version": 1, "entries": []}
    entries = []
    current: dict[str, str] | None = None
    in_entries = False
    version = 1
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = _strip_comment(raw)
        if not line.strip():
            continue
        stripped = line.strip()
        if stripped == "entries: []":
            if version != 1:
                raise ManifestError(f"unsupported lockfile version {version}")
            return {"version": version, "entries": []}
        if re.match(r"^version:\s*", stripped):
            value = _unquote(stripped.split(":", 1)[1])
            try:
                version = int(value)
            except ValueError as exc:
                raise ManifestError(
                    f"line {lineno}: lockfile version must be an int"
                ) from exc
            continue
        if stripped == "entries:":
            in_entries = True
            continue
        if not in_entries:
            continue
        if stripped.startswith("- "):
            if current:
                entries.append(_finalize_lock_entry(current))
            current = {}
            rest = stripped[2:].strip()
            if rest:
                key, _, value = rest.partition(":")
                current[key.strip()] = _unquote(value)
            continue
        if current is None:
            raise ManifestError(f"line {lineno}: lockfile field without an item")
        key, _, value = stripped.partition(":")
        current[key.strip()] = _unquote(value)
    if current:
        entries.append(_finalize_lock_entry(current))
    if version != 1:
        raise ManifestError(f"unsupported lockfile version {version}")
    return {"version": version, "entries": entries}


def _finalize_lock_entry(current: dict[str, str]) -> dict[str, str]:
    source = current.get("source")
    if not source:
        raise ManifestError("lockfile entry missing source")
    parsed = parse_source(source)
    sha = current.get("resolved_sha") or ""
    if sha and not re.fullmatch(r"[0-9a-fA-F]{7,40}", sha):
        raise ManifestError(f"invalid resolved_sha '{sha}'")
    return {
        "source": parsed["source"],
        "resolved_sha": sha.lower(),
        "synced_at": current.get("synced_at") or "",
    }


def dump_lockfile(entries: list[dict[str, str]]) -> str:
    lines = ["version: 1"]
    if not entries:
        lines.append("entries: []")
        lines.append("")
        return "\n".join(lines)
    lines.append("entries:")
    for entry in entries:
        lines.append(f"  - source: {entry['source']}")
        if entry.get("resolved_sha"):
            lines.append(f"    resolved_sha: {entry['resolved_sha']}")
        if entry.get("synced_at"):
            lines.append(f"    synced_at: {entry['synced_at']}")
    lines.append("")
    return "\n".join(lines)


def lockfile_index(lock: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {e["source"]: e for e in lock.get("entries") or []}


def _read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] not in {"manifest", "lockfile", "source"}:
        print(
            "usage: parse_manifest.py manifest|lockfile|source <file-or-string>",
            file=sys.stderr,
        )
        return 64
    mode, target = argv[0], argv[1]
    if mode == "source":
        print(parse_source(target)["path"])
        return 0
    text = sys.stdin.read() if target == "-" else _read_file(target)
    data = parse_manifest(text) if mode == "manifest" else parse_lockfile(text)
    import json

    json.dump(data, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except ManifestError as exc:
        print(f"parse error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
