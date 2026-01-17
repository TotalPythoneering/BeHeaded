#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./create_repo.sh [OWNER] [REPO] [VISIBILITY] [BRANCH] [COMMIT_MSG] [LICENSE]
# Defaults:
OWNER=${1:-soft9000}
REPO=${2:-beheaded}
VISIBILITY=${3:-public}   # public or private
BRANCH=${4:-main}
COMMIT_MSG=${5:-"Initial import — add pyhead_tui, README and CI"}
LICENSE=${6:-mit}        # SPDX id (mit, apache-2.0, gpl-3.0, etc)

mkdir -p "$REPO"
cd "$REPO"

# README
cat > README.md <<'README'
# pyhead-tui

A small Python TUI (text-based interactive CLI) to read, view, and update the top-of-file comment header of any Python script into an ordered dictionary.

Features
- Parses the contiguous comment block at the top of a Python file (optionally preserving a shebang).
- Treats lines that begin with a colon (after removing the leading `#`) as a tag: e.g. `# :author`
- Subsequent non-tag comment lines belong to the most recent tag (collected as the tag's value).
- Preserves "preamble" comment lines (comment lines before the first `:tag`).
- Interactive REPL to list tags, view, edit (via $EDITOR), add or delete tags, and write changes back to the script.
- Keeps tag order.

Usage
1. Run the script: