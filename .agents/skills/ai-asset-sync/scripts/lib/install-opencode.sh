#!/usr/bin/env bash
# install-opencode.sh — shared opencode CLI installer (adapted from
# smooth-ai-report-review LADR-048). Single source of truth for this skill.
#
# Inputs (env, optional):
#   OPENCODE_CLI_VERSION — version pin (leading `v` stripped); blank → latest.
#   GITHUB_PATH          — set by GitHub Actions; appended so later steps find opencode.
set -euo pipefail

REQUESTED_VERSION=""
if [ -n "${OPENCODE_CLI_VERSION:-}" ]; then
  REQUESTED_VERSION="${OPENCODE_CLI_VERSION#v}"
else
  REQUESTED_VERSION="latest"
fi
echo "Requested opencode version: ${REQUESTED_VERSION}"

install_needed="false"
if command -v opencode >/dev/null 2>&1; then
  cached_version="$(opencode --version 2>/dev/null | grep -Eo 'v?[0-9]+(\.[0-9]+){1,3}([.-][0-9A-Za-z]+)?' | head -1 | sed 's/^v//' || true)"
  if [ -n "$cached_version" ] && { [ "$REQUESTED_VERSION" = "latest" ] || [ "$cached_version" = "$REQUESTED_VERSION" ]; }; then
    echo "✓ opencode found on PATH (version: $cached_version)"
    exit 0
  fi
  install_needed="true"
else
  install_needed="true"
fi

if [ "$install_needed" = "true" ]; then
  echo "Installing opencode (${REQUESTED_VERSION})..."
  if [ "$REQUESTED_VERSION" = "latest" ]; then
    if ! curl -fsSL https://opencode.ai/install | bash; then
      echo "❌ opencode install failed." >&2
      exit 1
    fi
  else
    if ! curl -fsSL https://opencode.ai/install | bash -s -- --version "$REQUESTED_VERSION"; then
      echo "❌ opencode install failed." >&2
      exit 1
    fi
  fi
fi

if [ -x "$HOME/.opencode/bin/opencode" ] && ! command -v opencode >/dev/null 2>&1; then
  export PATH="$HOME/.opencode/bin:$PATH"
  echo "$HOME/.opencode/bin" >> "${GITHUB_PATH:-/dev/null}"
fi

if ! command -v opencode >/dev/null 2>&1; then
  echo "❌ opencode is not on PATH after install." >&2
  exit 1
fi
installed_version="$(opencode --version | grep -Eo 'v?[0-9]+(\.[0-9]+){1,3}([.-][0-9A-Za-z]+)?' | head -1 | sed 's/^v//' || true)"
if [ -z "$installed_version" ]; then
  echo "❌ Unable to determine installed opencode version." >&2
  exit 1
fi
if [ "$REQUESTED_VERSION" != "latest" ] && [ "$installed_version" != "$REQUESTED_VERSION" ]; then
  echo "❌ opencode version mismatch: expected ${REQUESTED_VERSION}, got ${installed_version}." >&2
  exit 1
fi
echo "✓ opencode ready (version: ${installed_version})"
