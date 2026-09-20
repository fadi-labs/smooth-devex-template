#!/usr/bin/env bash
# Skill: create-worktask
# Deterministic scaffolder for a worktask file under .context/work-tasks/.
#
# Creates .context/work-tasks/<slug>.md from the skill's asset template with
# placeholder substitution, then prints a JSON object of the created path.
# Refuses to overwrite an existing worktask unless --force is passed.
#
# Tool agnostic: bash + coreutils only. Repo root discovered via git.
# The skill carries the *judgment* (which contexts to list, what requirements
# and acceptance criteria to capture); this script only lays down the skeleton.

set -euo pipefail

SCRIPT_DIR=$(cd -P "$(dirname "$0")" && pwd -P)
SKILL_DIR=$(cd -P "$SCRIPT_DIR/.." && pwd -P)
ASSETS_DIR="$SKILL_DIR/assets"

SLUG=""
TITLE=""
FORCE=0

usage() {
    cat <<'USAGE'
Usage:
  scaffold-worktask.sh <kebab-case-slug> [--title "Human Title"] [--force]

Arguments:
  <kebab-case-slug>   Lowercase, hyphen-separated, e.g. add-vessel-eta-validation
                      Produces .context/work-tasks/<slug>.md

Options:
  --title "..."       One-liner task description for the H1.
                      Defaults to the slug with hyphens replaced by spaces.
  --force             Overwrite an existing worktask file of the same name.

Output:
  JSON object on stdout with the slug, title, and created path.
USAGE
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        -h|--help) usage; exit 0 ;;
        --title) [ "$#" -ge 2 ] || { echo "Error: --title requires a value." >&2; usage >&2; exit 2; }; TITLE="$2"; shift 2 ;;
        --force) FORCE=1; shift ;;
        --) shift; break ;;
        -*) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
        *)
            if [ -z "$SLUG" ]; then SLUG="$1"; shift
            else echo "Unexpected argument: $1" >&2; usage >&2; exit 2; fi
            ;;
    esac
done

[ -n "$SLUG" ] || { echo "Error: slug is required." >&2; usage >&2; exit 2; }

# Validate kebab-case: lowercase letters, digits, single hyphens; no leading/trailing/double hyphen.
if ! printf '%s' "$SLUG" | grep -Eq '^[a-z0-9]+(-[a-z0-9]+)*$'; then
    echo "Error: slug must be kebab-case (lowercase letters, digits, single hyphens): '$SLUG'" >&2
    exit 2
fi

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
WORKTASK_ROOT="$REPO_ROOT/.context/work-tasks"
mkdir -p "$WORKTASK_ROOT"

TARGET="$WORKTASK_ROOT/${SLUG}.md"
if [ -e "$TARGET" ] && [ "$FORCE" -eq 0 ]; then
    echo "Error: worktask already exists: $TARGET (pass --force to overwrite)" >&2
    exit 1
fi

# Derive title from slug if not supplied: hyphens -> spaces, first word capitalized.
if [ -z "$TITLE" ]; then
    TITLE=$(printf '%s' "$SLUG" | tr '-' ' ' | awk '{ $1=toupper(substr($1,1,1)) substr($1,2) } 1')
fi
# Reject control characters (tab/newline/CR/...) in the title: they would break the
# sed program and the generated JSON.
if printf '%s' "$TITLE" | LC_ALL=C grep -q '[[:cntrl:]]'; then
    echo "Error: title must not contain control characters (tab/newline/...)." >&2
    exit 2
fi

DATE=$(date +%F)

# Escape a string for use in a sed replacement (delimiter '|'): backslash,
# ampersand, and the '|' delimiter are special and must be backslash-escaped.
sed_escape() { printf '%s' "$1" | sed -e 's/[\\&|]/\\&/g'; }
# Escape a string for embedding inside a JSON double-quoted string.
json_escape() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'; }

TITLE_SED=$(sed_escape "$TITLE")

SRC="$ASSETS_DIR/WORKTASK.template.md"
[ -f "$SRC" ] || { echo "Error: missing template: $SRC" >&2; exit 1; }

# Placeholders: {{TITLE}} {{SLUG}} {{DATE}}
sed -e "s|{{TITLE}}|${TITLE_SED}|g" \
    -e "s|{{SLUG}}|${SLUG}|g" \
    -e "s|{{DATE}}|${DATE}|g" \
    "$SRC" > "$TARGET"

# Emit JSON (path relative to repo root for portability).
rel() { printf '%s' "${1#"$REPO_ROOT"/}"; }
printf '{\n'
printf '  "slug": "%s",\n' "$SLUG"
printf '  "title": "%s",\n' "$(json_escape "$TITLE")"
printf '  "created": "%s"\n' "$(rel "$TARGET")"
printf '}\n'
