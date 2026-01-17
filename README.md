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
   ```
   python pyhead_tui.py path/to/script.py
   ```
   If no path is provided, you'll be prompted to enter one.

2. Commands inside the REPL:
   - help             Show help
   - list             List all tags (and a short preview)
   - show <tag>       Show full value for a tag (or `preamble` to see preamble)
   - edit <tag>       Edit a tag's value in $EDITOR (creates tag if missing)
   - set <tag>        Set value inline (multi-line input; finish with a single `.` on a line)
   - add <tag>        Add an empty tag
   - delete <tag>     Delete a tag
   - dump             Print the whole dictionary as JSON
   - write            Write the updated header back to the file (keeps shebang and remainder)
   - reload           Re-read the file (discarding unsaved changes)
   - quit / exit      Exit the program

Notes
- The editor used by `edit` is taken from the `EDITOR` environment variable (defaults to `vi`).
- When writing back to the file the header is rebuilt from the tags and preamble. Formatting produced places `# :tag` for tags and `# value` for values, with one blank comment line after the header.

Example header this tool understands:
```py
#!/usr/bin/env python
# Some preamble text
# :author
# Alice <alice@example.com>
# :description
# A short description of the script
# More description text for the same tag
```

This will parse into:
- preamble: ["Some preamble text"]
- author: ["Alice <alice@example.com>"]
- description: ["A short description of the script", "More description text for the same tag"]