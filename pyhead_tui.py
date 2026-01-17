#!/usr/bin/env python3
"""
pyhead_tui.py

TUI for reading and updating the top-of-file comments of a Python script.
"""

import sys
import os
import shutil
import json
import tempfile
import subprocess
import re
from collections import OrderedDict
from datetime import datetime

PROMPT = "pyhead> "

def read_file_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()

def write_file_lines(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)

def _normalize_tag(tag_raw: str) -> str:
    """
    Normalize tag name according to PYHEAD_TAG_TRANSFORM env var.

    Supported transforms:
      - snake  (default): lower-case and convert whitespace to underscores
      - lower            : lower-case only (whitespace preserved)
      - preserve         : preserve tag exactly as provided (trimmed)
    """
    mode = os.environ.get("PYHEAD_TAG_TRANSFORM", "snake").lower()
    tag = tag_raw.strip()
    if mode == "preserve":
        return tag
    if mode == "lower":
        return tag.lower()
    # default: snake
    return re.sub(r"\s+", "_", tag).lower()

def _current_datetime_str():
    # YYYY-MM-DD HH:MM:SS
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def parse_header(lines):
    """
    Parse the top-of-file comment header.

    Returns:
      shebang_line (str or None),
      header_end_index (int)  # index in original lines where header ends (the first non-comment line)
      preamble (list of str),
      tags (OrderedDict of tag -> list of str)
    """
    shebang = None
    idx = 0
    n = len(lines)
    if n == 0:
        return None, 0, [], OrderedDict()

    # preserve shebang line if present
    if lines[0].startswith("#!"):
        shebang = lines[0].rstrip("\n")
        idx = 1

    header_lines = []
    while idx < n:
        line = lines[idx]
        if line.lstrip().startswith("#"):
            header_lines.append(line.rstrip("\n"))
            idx += 1
        else:
            # first non-comment line -> header ends
            break

    # parse header lines: strip leading '#' and one optional space
    preamble = []
    tags = OrderedDict()
    current_tag = None

    # regex to match "FirstWord: rest-of-line" where FirstWord contains no whitespace/colon
    firstword_colon_re = re.compile(r'^\s*([^\s:]+)\s*:\s*(.*)$')

    for raw in header_lines:
        content = raw.lstrip()
        if content.startswith("#"):
            content = content[1:]
        if content.startswith(" "):
            content = content[1:]
        content = content.rstrip("\n")

        # 1) legacy ":tag" marker (colon at start) - allow multi-word tag after the starting colon
        if content.strip().startswith(":"):
            tag_part = content.strip()[1:].strip()
            if tag_part == "":
                current_tag = None
                continue
            tag_key = _normalize_tag(tag_part)
            tags.setdefault(tag_key, [])
            current_tag = tag_key
            continue

        # 2) "FirstWord: rest" detection (first colon after the first word)
        m = firstword_colon_re.match(content)
        if m:
            tag_part = m.group(1).strip()
            rest = m.group(2).rstrip()
            tag_key = _normalize_tag(tag_part)
            tags.setdefault(tag_key, [])
            if rest != "":
                tags[tag_key].append(rest)
            current_tag = tag_key
            continue

        # 3) ordinary comment line: either preamble or part of current tag
        if current_tag is None:
            preamble.append(content)
        else:
            tags[current_tag].append(content)

    return shebang, idx, preamble, tags

def _ensure_default_tags(state):
    """
    Ensure certain tags exist in state['tags'] with defaults if missing, and always update DATE.

    Defaults:
      - FILE: basename of the file (os.path.basename(state['path']))
      - MISSION: "tbd."
      - STATUS: "tbd."
      - NOTES: "tbd."
      - VERSION: "0.0.0"
      - DATE: current date/time (always updated)
    Insert missing tags as single-value lists. Tag keys are normalized.
    """
    path = state.get("path", "")
    tags = state.get("tags", OrderedDict())

    # desired defaults in order (key=raw name, value default string or callable)
    defaults = [
        ("FILE", lambda: os.path.basename(path) if path else ""),
        ("VERSION", lambda: "0.0.0"),
        ("DATE", _current_datetime_str),  # always updated
        ("MISSION", lambda: "tbd."),
        ("STATUS", lambda: "tbd."),
        ("NOTES", lambda: "tbd."),
    ]

    for raw_name, value_fn in defaults:
        key = _normalize_tag(raw_name)
        val = value_fn()
        if raw_name == "DATE":
            # always set/update DATE
            tags[key] = [val]
        else:
            if key not in tags or not tags[key]:
                tags[key] = [val]

    # write back updated tags
    state["tags"] = tags

def build_header_lines(shebang, preamble, tags):
    out = []
    if shebang:
        out.append(shebang.rstrip("\n") + "\n")
    for p in preamble:
        out.append("# " + p.rstrip("\n") + "\n")
    for tag, values in tags.items():
        out.append("# :" + tag + "\n")
        for v in values:
            out.append("# " + v.rstrip("\n") + "\n")
    # ensure a single blank line after header if there is any header
    if out and (not out[-1].endswith("\n") or out[-1].strip() != ""):
        out.append("\n")
    if out and not out[-1].strip() == "":
        out.append("\n")
    # Trim duplicate trailing blank lines to a single blank line
    if len(out) >= 2 and out[-1].strip() == "" and out[-2].strip() == "":
        while len(out) >= 2 and out[-1].strip() == "" and out[-2].strip() == "":
            out.pop(-2)
    return out

def load_header_from_file(path):
    lines = read_file_lines(path)
    shebang, header_end, preamble, tags = parse_header(lines)
    state = {
        "path": path,
        "lines": lines,
        "shebang": shebang,
        "header_end": header_end,
        "preamble": preamble,
        "tags": tags
    }
    # ensure defaults (adds/updates tags like FILE, VERSION, DATE, MISSION, STATUS, NOTES)
    _ensure_default_tags(state)
    return state

def show_tags(state):
    tags = state["tags"]
    if not tags and not state["preamble"]:
        print("(no tags or preamble found)")
        return
    if state["preamble"]:
        preview = " | ".join(line.strip() for line in state["preamble"][:2])
        print(f"preamble: {preview}")
    for tag, vals in tags.items():
        preview = " | ".join(v.strip() for v in vals[:2])
        print(f"{tag}: {preview}")

def show_tag(state, tag):
    if tag == "preamble":
        if not state["preamble"]:
            print("(no preamble)")
            return
        print("--- preamble ---")
        for line in state["preamble"]:
            print(line)
        print("---------------")
        return
    tag_key = _normalize_tag(tag)
    tags = state["tags"]
    if tag_key not in tags:
        print(f"(tag '{tag}' not found)")
        return
    print(f"--- :{tag_key} ---")
    for line in tags[tag_key]:
        print(line)
    print("--------------")

def edit_tag_via_editor(state, tag):
    tag_key = _normalize_tag(tag)
    cur = []
    if tag_key == "preamble":
        cur = state["preamble"]
    else:
        cur = state["tags"].get(tag_key, [])
    editor = os.environ.get("EDITOR", "vi")
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".tmp", encoding="utf-8") as tf:
        tempname = tf.name
        tf.write("\n".join(cur))
        tf.flush()
    try:
        rc = subprocess.call([editor, tempname])
        if rc != 0:
            print(f"(editor exited with code {rc})")
        with open(tempname, "r", encoding="utf-8") as f:
            new = f.read().splitlines()
    finally:
        try:
            os.unlink(tempname)
        except Exception:
            pass
    if tag_key == "preamble":
        state["preamble"] = new
    else:
        state["tags"][tag_key] = new
    print(f"(updated '{tag_key}')")

def set_tag_inline(state, tag):
    tag_key = _normalize_tag(tag)
    print("Enter lines. End with a single dot on a line '.'")
    lines = []
    while True:
        try:
            ln = input()
        except EOFError:
            break
        if ln.strip() == ".":
            break
        lines.append(ln)
    if tag_key == "preamble":
        state["preamble"] = lines
    else:
        state["tags"][tag_key] = lines
    print(f"(set {len(lines)} lines for '{tag_key}')")

def add_tag(state, tag):
    tag_key = _normalize_tag(tag)
    if tag_key in state["tags"]:
        print("(tag already exists)")
    else:
        state["tags"][tag_key] = []
        print("(tag added)")

def delete_tag(state, tag):
    tag_key = _normalize_tag(tag)
    if tag_key == "preamble":
        state["preamble"] = []
        print("(preamble cleared)")
        return
    if tag_key in state["tags"]:
        del state["tags"][tag_key]
        print("(tag deleted)")
    else:
        print("(tag not found)")

def dump_json(state):
    serial = OrderedDict()
    if state["preamble"]:
        serial["preamble"] = state["preamble"]
    for k, v in state["tags"].items():
        serial[k] = v
    print(json.dumps(serial, indent=2, ensure_ascii=False))

def write_back(state):
    path = state["path"]
    original_lines = state["lines"]
    shebang = state["shebang"]
    header_end = state["header_end"]
    preamble = state["preamble"]
    tags = state["tags"]
    new_header_lines = build_header_lines(shebang, preamble, tags)
    rest = original_lines[header_end:]
    new_lines = new_header_lines + rest
    backup = path + ".bak"
    try:
        shutil.copy2(path, backup)
        write_file_lines(path, new_lines)
        print(f"(wrote header back to {path}; original saved to {backup})")
        new_state = load_header_from_file(path)
        state.update(new_state)
    except Exception as e:
        print("(error writing file):", e)

def repl(state):
    print("pyhead TUI - type 'help' for commands")
    while True:
        try:
            cmdline = input(PROMPT)
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not cmdline.strip():
            continue
        parts = cmdline.strip().split()
        cmd = parts[0].lower()
        args = parts[1:]
        if cmd in ("quit", "exit"):
            break
        elif cmd == "help":
            print("""Commands:
  help             Show this help
  list             List tags and previews
  show <tag>       Show full value for tag ('preamble' for preamble)
  edit <tag>       Edit tag value in $EDITOR (creates if missing)
  set <tag>        Set tag value inline (finish with a single '.' on a line)
  add <tag>        Add an empty tag
  delete <tag>     Delete a tag
  dump             Dump the parsed dictionary as JSON
  write            Write header back to file
  reload           Re-read the file (discarding unsaved changes)
  quit / exit      Exit
""")
        elif cmd == "list":
            show_tags(state)
        elif cmd == "show":
            if not args:
                print("usage: show <tag>")
                continue
            show_tag(state, args[0])
        elif cmd == "edit":
            if not args:
                print("usage: edit <tag>")
                continue
            tag = args[0]
            tag_key = _normalize_tag(tag)
            if tag_key != "preamble" and tag_key not in state["tags"]:
                state["tags"].setdefault(tag_key, [])
            edit_tag_via_editor(state, tag)
        elif cmd == "set":
            if not args:
                print("usage: set <tag>")
                continue
            set_tag_inline(state, args[0])
        elif cmd == "add":
            if not args:
                print("usage: add <tag>")
                continue
            add_tag(state, args[0])
        elif cmd == "delete":
            if not args:
                print("usage: delete <tag>")
                continue
            delete_tag(state, args[0])
        elif cmd == "dump":
            dump_json(state)
        elif cmd == "write":
            write_back(state)
        elif cmd == "reload":
            new_state = load_header_from_file(state["path"])
            state.update(new_state)
            print("(reloaded)")
        else:
            print("(unknown command)")

def main(argv):
    if len(argv) >= 2:
        path = argv[1]
    else:
        path = input("Path to python file: ").strip()
    if not path:
        print("No path provided; exiting.")
        return 1
    if not os.path.isfile(path):
        print("File not found:", path)
        return 1
    state = load_header_from_file(path)
    repl(state)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))