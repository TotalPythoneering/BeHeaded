# pyhead-tui

[![CI](https://github.com/soft9000/beheaded/actions/workflows/ci.yml/badge.svg)](https://github.com/soft9000/beheaded/actions)

A small Python TUI (text-based interactive CLI) to read, view, and update the top-of-file comment header of any Python script into an ordered dictionary.

Features
- Parses the contiguous comment block at the top of a Python file (optionally preserving a shebang).
- Supports two tag styles:
  - legacy colon-marker: `# :tag` (multi-word tags allowed after the leading colon)
  - first-word-colon: `# TagName: value` — treat first word before the first colon as the tag name and capture inline value as the first value
- Subsequent comment lines belong to the current tag until a new tag is encountered.
- Tag name normalization configurable via environment variable.
- Interactive REPL to list, show, edit (in $EDITOR), set, add, delete tags and write changes back into the file.

Tag syntax supported
- Legacy marker style:
  - `# :tag` — a tag marker line. Everything after the marker (on subsequent comment lines) becomes that tag's values.
  - Example:
    ```
    # :author
    # Alice
    ```

- First-word colon style:
  - `# Word: rest-of-line` — if a colon appears immediately after the first word, the first word is treated as the tag name and any text after the colon on the same line is captured as the first value.
  - Example:
    ```
    # Author: Alice <alice@example.com>
    # Biography line 1
    ```

Tag normalization and configuration
- By default tag names are normalized to snake_case:
  - lowercased and spaces converted to underscores
  - Example: `# :Author Name` → tag key `author_name`
- You can control normalization via the environment variable `PYHEAD_TAG_TRANSFORM`:
  - `snake` (default) — lower-case and convert whitespace to underscores
  - `lower` — lower-case only (spaces preserved)
  - `preserve` — keep tag name exactly as provided (trimmed)
- Examples:
  - `export PYHEAD_TAG_TRANSFORM=preserve`
  - `export PYHEAD_TAG_TRANSFORM=lower`

Behavior specifics
- Inline values after the colon (e.g. `# Author: Alice`) are captured as the first value for the tag.
- Subsequent comment lines (until a new tag) are appended as additional values for the active tag.
- Tag keys are the normalized versions of the tag label (see normalization above).
- When writing the header back to a file the header is rebuilt using `# :tag` markers for tags and `# value` for tag values (the writer uses normalized tag keys).

Usage
1. Run the script:
   ```
   python pyhead_tui.py path/to/script.py
   ```
2. Commands inside the REPL:
   - help, list, show <tag>, edit <tag>, set <tag>, add <tag>, delete <tag>, dump, write, reload, quit

Developer / testing
- Dev requirements are in `requirements-dev.txt` (black, flake8, pytest).
- To run tests locally:
  ```
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements-dev.txt
  pytest -q
  ```
- Tests added:
  - `tests/test_pyhead_edgecases.py` — parsing edge cases and normalization behavior
  - `tests/test_writeback_and_editor.py` — write_back behavior and editor-simulated updates

Examples
- Parsing inline tag and multi-line values:
  ```
  #!/usr/bin/env python
  # Some preamble
  # Author: Alice <alice@example.com>
  # More author notes
  ```
  This parses to:
  - preamble: ["Some preamble"]
  - tags["author"] == ["Alice <alice@example.com>", "More author notes"]

Configuration example
- Preserve exact tag names:
  ```
  export PYHEAD_TAG_TRANSFORM=preserve
  python pyhead_tui.py path/to/script.py
  ```

Notes
- The tool normalizes tags for consistent keys by default. If you prefer a different behavior, set `PYHEAD_TAG_TRANSFORM` accordingly.
- The write-back uses normalized tag keys as `# :<normalized-key>` markers. If you want a different write style (preserve original tag label in output), let me know and I can add support to retain original tag labels on write.