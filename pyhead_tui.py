#!/usr/bin/env python3
"""
pyhead_tui.py

TUI for reading and updating the top-of-file comments of a Python script.
See README.md for usage.
"""

import sys
import os
import shutil
import json
import tempfile
import subprocess
from collections import OrderedDict

PROMPT = "pyhead> "

def read_file_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()

def write_file_lines(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)

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
            # first non-comment (or empty non-comment) line -> header ends
            break

    # parse header lines: strip leading '#' and one optional space
    preamble = []
    tags = OrderedDict()
    current_tag = None

    for raw in header_lines:
        # remove leading '#' and one space if present
        content = raw.lstrip()
        if content.startswith("#"):
            content = content[1:]
        # strip single leading space
        if content.startswith(" "):
            content = content[1:]
        content = content.rstrip("\n")
        if content.strip().startswith(":"):
            tag = content.strip()[1:].strip()
            if tag == "":
                # ignore empty tag markers
                current_tag = None
                continue
            if tag not in tags:
                tags[tag] = []
            current_tag = tag
        else:
            # a normal comment line
            if current_tag is None:
                preamble.append(content)
            else:
                tags[current_tag].append(content)

    return shebang, idx, preamble, tags

def build_header_lines(shebang, preamble, tags):
    """
    Build comment header lines (with trailing newline characters).
    Returns list of lines (strings with newline).
    """
    out = []
    if shebang:
        out.append(shebang.rstrip("\n") + "\n")
    # write preamble
    for p in preamble:
        out.append("# " + p.rstrip("\n") + "\n")
    if preamble and tags:
        # add a separating comment line? We'll not add extra; keep as-is
        pass
    # write tags
    for tag, values in tags.items():
        out.append("# :" + tag + "\n")
        for v in values:
            out.append("# " + v.rstrip("\n") + "\n")
    # ensure a single blank line after header if there is any header
    if out and (not out[-1].endswith("\n") or out[-1].strip() != ""):
        out.append("\n")
    # Guarantee at least one newline separator
    if out and not out[-1].strip() == "":
        out.append("\n")
    # Trim duplicate trailing blank lines to a single blank line
    if len(out) >= 2 and out[-1].strip() == "" and out[-2].strip() == "":
        # remove extra
        while len(out) >= 2 and out[-1].strip() == "" and out[-2].strip() == "":
            out.pop(-2)
    return out

def load_header_from_file(path):
    lines = read_file_lines(path)
    shebang, header_end, preamble, tags = parse_header(lines)
    return {
        "path": path,
        "lines": lines,
        "shebang": shebang,
        "header_end": header_end,
        "preamble": preamble,
        "tags": tags
    }

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
    tags = state["tags"]
    if tag not in tags:
        print(f"(tag '{tag}' not found)")
        return
    print(f"--- :{tag} ---")
    for line in tags[tag]:
        print(line)
    print("--------------")

def edit_tag_via_editor(state, tag):
    # create temp file with current contents
    cur = []
    if tag == "preamble":
        cur = state["preamble"]
    else:
        cur = state["tags"].get(tag, [])
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
    if tag == "preamble":
        state["preamble"] = new
    else:
        state["tags"][tag] = new
    print(f"(updated '{tag}')")

def set_tag_inline(state, tag):
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
    if tag == "preamble":
        state["preamble"] = lines
    else:
        state["tags"][tag] = lines
    print(f"(set {len(lines)} lines for '{tag}')")

def add_tag(state, tag):
    if tag in state["tags"]:
        print("(tag already exists)")
    else:
        state["tags"][tag] = []
        print("(tag added)")

def delete_tag(state, tag):
    if tag == "preamble":
        state["preamble"] = []
        print("(preamble cleared)")
        return
    if tag in state["tags"]:
        del state["tags"][tag]
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
    # append the remainder of the file from header_end
    rest = original_lines[header_end:]
    new_lines = new_header_lines + rest
    # Backup original file
    backup = path + ".bak"
    try:
        shutil.copy2(path, backup)
        write_file_lines(path, new_lines)
        print(f"(wrote header back to {path}; original saved to {backup})")
        # reload state
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
  reload           Re-read the file (discard unsaved changes)
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
            if tag != "preamble" and tag not in state["tags"]:
                # create so the editor starts empty
                state["tags"].setdefault(tag, [])
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