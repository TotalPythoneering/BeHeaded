#!/usr/bin/env bash
set -euo pipefail

# create_repo.sh
# Bootstraps the full repository "beheaded" with all files, CI, tests, and commits/pushes.
#
# Usage:
#   ./create_repo.sh [OWNER] [REPO] [VISIBILITY] [BRANCH] [COMMIT_MSG] [LICENSE]
#
# Defaults:
#   OWNER=soft9000
#   REPO=beheaded
#   VISIBILITY=public
#   BRANCH=main
#   COMMIT_MSG="Initial import — add pyhead_tui, README, CI, tests and .gitignore"
#   LICENSE=mit

OWNER=${1:-soft9000}
REPO=${2:-beheaded}
VISIBILITY=${3:-public}
BRANCH=${4:-main}
COMMIT_MSG=${5:-"Initial import — add pyhead_tui, README, CI, tests and .gitignore"}
LICENSE=${6:-mit}

# Create project directory
mkdir -p "$REPO"
cd "$REPO"

# README.md
cat > README.md <<'README'
# pyhead-tui

[![CI](https://github.com/soft9000/beheaded/actions/workflows/ci.yml/badge.svg)](https://github.com/soft9000/beheaded/actions)

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