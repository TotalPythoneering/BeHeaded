#!/usr/bin/env python3
"""
Core implementation for BeHeaded.

This module implements:
- parsing and writing header comment blocks
- per-folder .BeHeaders.json defaults
- CLI and interactive mainloop functions

Public functions expected by tests and package users:
- read_file_header
- write_header_to_file
- add_default_header_to_file
- read_bejson_for_folder
- get_wrap_width_from_defaults
- file_mtime_string
- bump_version_in_file
- bump_version_in_tree
- apply_defaults_recursively
- cli_main
- mainloop
"""
from __future__ import annotations
import argparse
import os
import re
import sys
import json
import textwrap
import tempfile
import subprocess
from datetime import datetime
from typing import List, Dict, Tuple, Optional

DEFAULT_ORDER = ["MISSION", "STATUS", "VERSION", "NOTES", "DATE", "FILE", "AUTHOR"]
STATUS_ALLOWED = ["Production", "Testing", "Research"]
DEFAULT_WRAP = 72
BEJSON_NAME = ".BeHeaders.json"
VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
KEY_RE = re.compile(r"^([A-Z]+):\s?(.*)$")


def find_python_files(start: str, recurse: bool = False) -> List[str]:
    py_files: List[str] = []
    if os.path.isfile(start) and start.endswith(".py"):
        py_files.append(os.path.abspath(start))
        return py_files
    if os.path.isdir(start):
        if recurse:
            for root, _, files in os.walk(start):
                for f in files:
                    if f.endswith(".py"):
                        py_files.append(os.path.join(root, f))
        else:
            for f in os.listdir(start):
                p = os.path.join(start, f)
                if f.endswith(".py") and os.path.isfile(p):
                    py_files.append(p)
    return sorted(py_files)


def read_bejson_for_folder(folder: str) -> Dict[str, object]:
    """
    Read or create per-folder .BeHeaders.json.
    Returns a dict keyed by UPPER-CASE keys. If the file contains non-dict or invalid JSON,
    returns {}.
    """
    path = os.path.join(folder, BEJSON_NAME)
    if not os.path.exists(path):
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump({}, fh, indent=2)
        except Exception:
            pass
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            try:
                data = json.load(fh)
                if not isinstance(data, dict):
                    return {}
                out: Dict[str, object] = {}
                for k, v in data.items():
                    out[str(k).upper()] = v
                return out
            except json.JSONDecodeError:
                return {}
    except Exception:
        return {}


def file_mtime_string(path: str) -> str:
    try:
        mtime = os.path.getmtime(path)
        dt = datetime.fromtimestamp(mtime)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Header:
    def __init__(self):
        self.key_order: List[str] = []
        self.values: Dict[str, str] = {}
        self.raw_comment_lines: List[str] = []

    def set(self, key: str, value: str):
        k = key.upper()
        if k not in self.key_order:
            self.key_order.append(k)
        self.values[k] = value

    def get(self, key: str) -> Optional[str]:
        return self.values.get(key.upper())

    def has(self, key: str) -> bool:
        return key.upper() in self.values

    def to_ordered_list(
        self, folder_defaults: Dict[str, object], file_path: Optional[str] = None
    ) -> List[Tuple[str, str]]:
        output: List[Tuple[str, str]] = []
        seen = set()

        def default_for(k: str) -> str:
            ku = k.upper()
            if ku == "FILE":
                return os.path.basename(file_path) if file_path else "tbd."
            if ku in folder_defaults and folder_defaults[ku] not in (None, ""):
                return str(folder_defaults[ku])
            if ku == "VERSION":
                return "0.0.0"
            if ku == "DATE":
                return file_mtime_string(file_path) if file_path else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return "tbd."

        for k in DEFAULT_ORDER:
            val = self.values.get(k)
            if val is None:
                val = default_for(k)
            else:
                if k == "FILE":
                    val = os.path.basename(file_path) if file_path else default_for(k)
            output.append((k, val))
            seen.add(k)

        for k in self.key_order:
            if k not in seen:
                output.append((k, self.values.get(k, default_for(k))))
                seen.add(k)

        for k in list(self.values.keys()):
            if k not in seen:
                output.append((k, self.values[k]))
                seen.add(k)

        return output


def parse_header_from_lines(lines: List[str]) -> Tuple[Optional[str], Header, List[str]]:
    """
    Parse top-of-file header from given lines. Return (shebang_line_or_None, header_obj, rest_of_file_lines).
    Header block is contiguous comment lines starting at top after an optional shebang.
    This parser preserves blank comment lines and treats them as continuation lines (empty strings).
    """
    idx = 0
    shebang: Optional[str] = None
    n = len(lines)
    if n == 0:
        return None, Header(), []

    if lines[0].startswith("#!"):
        shebang = lines[0].rstrip("\n")
        idx = 1

    comment_block: List[str] = []
    while idx < n and lines[idx].lstrip().startswith("#"):
        comment_block.append(lines[idx].rstrip("\n"))
        idx += 1

    rest = [l.rstrip("\n") for l in lines[idx:]]
    header = Header()
    header.raw_comment_lines = list(comment_block)
    current_key: Optional[str] = None
    current_lines: List[str] = []

    for c in comment_block:
        if c.startswith("#"):
            content = c[1:]
            if content.startswith(" "):
                content = content[1:]
            content = content.rstrip("\n")
        else:
            content = c
        m = KEY_RE.match(content)
        if m:
            if current_key:
                header.set(current_key, "\n".join(current_lines).rstrip())
            current_key = m.group(1).upper()
            first_val = m.group(2) or ""
            current_lines = [first_val.rstrip()]
        else:
            if current_key:
                current_lines.append(content.rstrip())
            else:
                if not header.has("PREAMBLE"):
                    header.set("PREAMBLE", content.rstrip())
                else:
                    header.set("PREAMBLE", header.get("PREAMBLE") + "\n" + content.rstrip())
    if current_key:
        header.set(current_key, "\n".join(current_lines).rstrip())

    return shebang, header, rest


def read_file_header(path: str) -> Tuple[Optional[str], Header, List[str]]:
    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()
    return parse_header_from_lines(lines)


def get_wrap_width_from_defaults(folder_defaults: Dict[str, object]) -> int:
    w = folder_defaults.get("WRAP_WIDTH")
    try:
        if isinstance(w, int):
            return w
        if isinstance(w, str) and str(w).isdigit():
            return int(w)
    except Exception:
        pass
    return DEFAULT_WRAP


def write_header_to_file(path: str, shebang: Optional[str], header: Header, folder_defaults: Dict[str, object]) -> None:
    # read rest of file to preserve content after header
    with open(path, "r", encoding="utf-8") as fh:
        orig_lines = fh.readlines()

    _, _, rest = parse_header_from_lines([l.rstrip("\n") for l in orig_lines])

    # Ensure FILE matches filename
    header.set("FILE", os.path.basename(path))

    ordered = header.to_ordered_list(folder_defaults, file_path=path)
    wrap_width = get_wrap_width_from_defaults(folder_defaults)

    out_lines: List[str] = []
    if shebang:
        out_lines.append(shebang.rstrip("\n"))

    for key, val in ordered:
        if key == "PREAMBLE":
            for pl in str(val).splitlines():
                out_lines.append(f"# {pl}" if pl != "" else "#")
            continue

        if key == "MISSION":
            wrapped = textwrap.wrap(str(val), wrap_width) or [""]
            if wrapped:
                first, *restwrap = wrapped
                out_lines.append(f"# {key}: {first}")
                for wline in restwrap:
                    out_lines.append(f"# {wline}")
            else:
                out_lines.append(f"# {key}:")
        else:
            lines = str(val).splitlines()
            if lines:
                first, *restlines = lines
                out_lines.append(f"# {key}: {first}" if first != "" else f"# {key}:")
                for l in restlines:
                    out_lines.append(f"# {l}" if l != "" else "#")
            else:
                out_lines.append(f"# {key}:")

    out_lines.append("#")
    for r in rest:
        out_lines.append(r)

    with open(path, "w", encoding="utf-8") as fh:
        for l in out_lines:
            fh.write(l.rstrip("\n") + "\n")


def show_header_on_stdout(path: str) -> None:
    shebang, header, rest = read_file_header(path)
    print(f"File: {path}")
    if shebang:
        print(f"Shebang: {shebang}")
    folder_defaults = read_bejson_for_folder(os.path.dirname(path))
    for k, v in header.to_ordered_list(folder_defaults, file_path=path):
        print(f"{k}:")
        for line in str(v).splitlines():
            print("  " + line)
    print("---- file content (first 10 lines after header) ----")
    for i, line in enumerate(rest[:10], 1):
        print(f"{i:2d}: {line}")
    print("--------------------------------------------------")


def edit_multiline_with_editor(initial_text: str) -> str:
    editor = os.environ.get("EDITOR")
    if not editor:
        print("No $EDITOR set. Enter multi-line input; finish with a single '.' on its own line.")
        lines: List[str] = []
        while True:
            try:
                ln = input()
            except EOFError:
                break
            if ln == ".":
                break
            lines.append(ln)
        return "\n".join(lines).rstrip()
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".tmp", encoding="utf-8") as tf:
        tf_name = tf.name
        tf.write(initial_text or "")
        tf.flush()
    try:
        subprocess.call([editor, tf_name])
        with open(tf_name, "r", encoding="utf-8") as fh:
            content = fh.read().rstrip("\n")
    finally:
        try:
            os.unlink(tf_name)
        except Exception:
            pass
    return content


def interactive_edit_header(path: str) -> None:
    folder_defaults = read_bejson_for_folder(os.path.dirname(path))
    shebang, header, _ = read_file_header(path)
    ordered = header.to_ordered_list(folder_defaults, file_path=path)
    edit = {k: v for k, v in ordered}
    # ensure FILE reflects the actual filename
    edit["FILE"] = os.path.basename(path)
    print(f"Editing header for {path}. Enter to keep current value. Commands: .q to quit without saving, .w to save and exit.")
    while True:
        print("\nCurrent header values (first line shown):")
        for i, (k, v) in enumerate(edit.items(), 1):
            display = (str(v).splitlines()[0] if v else "")
            print(f"{i:2d}. {k}: {display}")
        choice = input("Select field number to edit, 's' to save, 'q' to quit without saving, 'b' to bump version: ").strip()
        if choice.lower() in ("q", ".q"):
            print("Aborting without saving.")
            return
        if choice.lower() in ("s", ".w"):
            new_header = Header()
            for k, v in edit.items():
                new_header.set(k, v if v is not None else "")
            status_val = new_header.get("STATUS")
            if status_val and status_val not in STATUS_ALLOWED:
                print(f"STATUS must be one of {STATUS_ALLOWED}. Current STATUS: {status_val}")
                confirm = input("Do you want to proceed anyway? (y/N): ").strip().lower()
                if confirm != "y":
                    print("Not saved.")
                    continue
            write_header_to_file(path, shebang, new_header, folder_defaults)
            print("Saved.")
            return
        if choice.lower() in ("b",):
            newv = bump_version_interactive(edit.get("VERSION", "0.0.0"))
            if newv:
                edit["VERSION"] = newv
                print(f"Bumped version to {newv}")
            continue
        try:
            idx = int(choice)
            if not (1 <= idx <= len(edit)):
                print("Invalid selection.")
                continue
            key = list(edit.keys())[idx - 1]
            cur = edit[key] or ""
            print(f"Editing {key}. Current value:\n{cur}")
            if key == "MISSION" or ("\n" in str(cur)):
                print("Opening editor for multi-line field (or use console entry if no $EDITOR).")
                val = edit_multiline_with_editor(str(cur))
            else:
                val = input("New value (empty to keep current): ").rstrip("\n")
                if val == "":
                    val = cur
            if key == "FILE":
                print("FILE is automatically set to the filename and cannot be edited.")
                val = os.path.basename(path)
            edit[key] = val
        except ValueError:
            print("Unknown command.")


def bump_version_interactive(current_version: str) -> Optional[str]:
    cur = (current_version.strip() if current_version else "0.0.0") or "0.0.0"
    m = VERSION_RE.match(cur)
    if not m:
        print(f"Current version '{cur}' is not in dotted numeric form. Reset to 0.0.0? (y/N)")
        if input().strip().lower() == "y":
            major, minor, patch = 0, 0, 0
        else:
            return None
    else:
        major, minor, patch = map(int, m.groups())
    print(f"Current version: {major}.{minor}.{patch}")
    part = input("Which part to bump? (major/minor/patch): ").strip().lower()
    if part not in ("major", "minor", "patch"):
        print("Invalid part.")
        return None
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


def bump_version_in_file(path: str, part: str) -> bool:
    folder_defaults = read_bejson_for_folder(os.path.dirname(path))
    shebang, header, _ = read_file_header(path)
    oldv = header.get("VERSION") or folder_defaults.get("VERSION") or "0.0.0"
    m = VERSION_RE.match(str(oldv).strip())
    if not m:
        major, minor, patch = 0, 0, 0
    else:
        major, minor, patch = map(int, m.groups())
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    else:
        return False
    newv = f"{major}.{minor}.{patch}"
    header.set("VERSION", newv)
    write_header_to_file(path, shebang, header, folder_defaults)
    return True


def bump_version_in_tree(start: str, part: str, dry_run: bool = False) -> List[str]:
    files = find_python_files(start, recurse=True)
    changed: List[str] = []
    for f in files:
        folder_defaults = read_bejson_for_folder(os.path.dirname(f))
        shebang, header, _ = read_file_header(f)
        oldv = header.get("VERSION") or folder_defaults.get("VERSION") or "0.0.0"
        m = VERSION_RE.match(str(oldv).strip())
        if not m:
            major, minor, patch = 0, 0, 0
        else:
            major, minor, patch = map(int, m.groups())
        if part == "major":
            major += 1
            minor = 0
            patch = 0
        elif part == "minor":
            minor += 1
            patch = 0
        else:
            patch += 1
        newv = f"{major}.{minor}.{patch}"
        if str(oldv).strip() != newv:
            header.set("VERSION", newv)
            if dry_run:
                changed.append(f"{f}: {oldv} -> {newv}")
            else:
                write_header_to_file(f, shebang, header, folder_defaults)
                changed.append(f"{f}: {oldv} -> {newv}")
    return changed


def remove_header_from_file(path: str) -> None:
    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()
    shebang, _, rest = parse_header_from_lines([l.rstrip("\n") for l in lines])
    out_lines: List[str] = []
    if shebang:
        out_lines.append(shebang)
    for r in rest:
        out_lines.append(r)
    with open(path, "w", encoding="utf-8") as fh:
        for l in out_lines:
            fh.write(l.rstrip("\n") + "\n")


def add_default_header_to_file(path: str, folder_defaults: Optional[Dict[str, object]] = None, dry_run: bool = False) -> bool:
    if folder_defaults is None:
        folder_defaults = read_bejson_for_folder(os.path.dirname(path))
    shebang, header, _ = read_file_header(path)
    changed = False
    for k in DEFAULT_ORDER:
        if not header.has(k):
            if k == "FILE":
                header.set(k, os.path.basename(path))
            elif k in folder_defaults and folder_defaults[k] not in (None, ""):
                header.set(k, str(folder_defaults[k]))
            else:
                if k == "VERSION":
                    header.set(k, "0.0.0")
                elif k == "DATE":
                    header.set(k, file_mtime_string(path))
                else:
                    header.set(k, "tbd.")
            changed = True
    header.set("FILE", os.path.basename(path))
    if changed and not dry_run:
        write_header_to_file(path, shebang, header, folder_defaults)
    elif not changed:
        current_file_val = header.get("FILE")
        if current_file_val != os.path.basename(path):
            if not dry_run:
                write_header_to_file(path, shebang, header, folder_defaults)
            changed = True
    return changed


def apply_defaults_recursively(start: str, dry_run: bool = False) -> List[str]:
    files = find_python_files(start, recurse=True)
    changed: List[str] = []
    for f in files:
        fd = read_bejson_for_folder(os.path.dirname(f))
        did = add_default_header_to_file(f, folder_defaults=fd, dry_run=dry_run)
        if did:
            changed.append(f)
    return changed


# CLI functions
def cli_main():
    parser = argparse.ArgumentParser(description="BeHeaded - manage python file header comments.")
    parser.add_argument("paths", nargs="*", help="Files or folders to operate on. If a single filename is provided with no options, interactive mainloop will be used.")
    parser.add_argument("--list", "-l", action="store_true", help="List python files in current directory (or provided path).")
    parser.add_argument("--show", "-s", metavar="FILE", help="Show parsed header for FILE.")
    parser.add_argument("--edit", "-e", metavar="FILE", help="Open interactive editor for FILE (non-mainloop, single file).")
    parser.add_argument("--add", "-a", metavar="FILE", help="Add default header to FILE (does not overwrite existing keys).")
    parser.add_argument("--remove", "-r", metavar="FILE", help="Remove header from FILE.")
    parser.add_argument("--recurse", "-R", metavar="PATH", nargs="?", const=".", help="Apply ops recursively starting at PATH (default current dir).")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes for recursive operations without writing files.")
    parser.add_argument("--bump", "-b", metavar=("PART", "FILE"), nargs=2, help="Bump VERSION in FILE. PART is major|minor|patch")
    parser.add_argument("--bump-all", metavar=("PART", "PATH"), nargs=2, dest="bump_all", help="Bump VERSION for all python files under PATH. PART is major|minor|patch")
    parser.add_argument("--apply-all-defaults", action="store_true", help="Apply default headers to all found python files (recursively in provided path).")
    parser.add_argument("--select", "-S", metavar="FILE", help="Start mainloop with FILE selected (always opens interactive mainloop).")
    args, _ = parser.parse_known_args()

    provided_flags = any([args.list, args.show, args.edit, args.add, args.remove, args.recurse,
                           args.bump, args.apply_all_defaults, args.select, getattr(args, "bump_all", None), args.dry_run])
    if (len(sys.argv) == 1) or (len(sys.argv) == 2 and os.path.isfile(sys.argv[1]) and not provided_flags) or (args.select and not provided_flags):
        start_file = None
        if len(sys.argv) == 2 and os.path.isfile(sys.argv[1]):
            start_file = os.path.abspath(sys.argv[1])
        if args.select:
            start_file = os.path.abspath(args.select)
        mainloop(start_file)
        return

    if args.list:
        target = args.paths[0] if args.paths else "."
        files = find_python_files(target, recurse=False)
        for f in files:
            print(f)
        return

    if args.show:
        if not os.path.exists(args.show):
            print(f"No such file: {args.show}")
            return
        show_header_on_stdout(args.show)
        return

    if args.edit:
        if not os.path.exists(args.edit):
            print(f"No such file: {args.edit}")
            return
        interactive_edit_header(args.edit)
        return

    if args.add:
        if not os.path.exists(args.add):
            print(f"No such file: {args.add}")
            return
        did = add_default_header_to_file(args.add)
        print("Added defaults (where missing)." if did else "No changes necessary.")
        return

    if args.remove:
        if not os.path.exists(args.remove):
            print(f"No such file: {args.remove}")
            return
        remove_header_from_file(args.remove)
        print("Header removed.")
        return

    if args.bump:
        part, filep = args.bump
        if part not in ("major", "minor", "patch"):
            print("Part must be one of major, minor, patch.")
            return
        if not os.path.exists(filep):
            print(f"No such file: {filep}")
            return
        ok = bump_version_in_file(filep, part)
        if ok:
            print("Version bumped.")
        else:
            print("Failed to bump.")
        return

    if args.bump_all:
        part, start = args.bump_all
        if part not in ("major", "minor", "patch"):
            print("Part must be one of major, minor, patch.")
            return
        start = start or "."
        changes = bump_version_in_tree(start, part, dry_run=args.dry_run)
        if args.dry_run:
            print("Dry-run. Changes that would be made:")
        for c in changes:
            print(c)
        print(f"{len(changes)} file(s) affected.")
        return

    if args.recurse:
        start = args.recurse or "."
        changes = apply_defaults_recursively(start, dry_run=args.dry_run)
        if args.dry_run:
            print("Dry-run. Files that would be changed:")
        for c in changes:
            print(c)
        print(f"{len(changes)} file(s) {'would be changed' if args.dry_run else 'changed'}.")
        return

    if args.apply_all_defaults:
        start = args.paths[0] if args.paths else "."
        changes = apply_defaults_recursively(start, dry_run=args.dry_run)
        if args.dry_run:
            print("Dry-run. Files that would be changed:")
        for c in changes:
            print(c)
        print(f"{len(changes)} file(s) {'would be changed' if args.dry_run else 'changed'}.")
        return

    parser.print_help()


def mainloop(start_file: Optional[str] = None):
    cwd = os.getcwd()
    files = find_python_files(cwd, recurse=False)
    selected: Optional[str] = None
    if start_file:
        selected = start_file

    print("BeHeaded interactive mainloop. Type 'help' for commands.")
    while True:
        prompt = f"[{os.path.basename(selected) if selected else 'no-file'}] > "
        try:
            cmdline = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            return
        if not cmdline:
            continue
        parts = cmdline.split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in ("q", "quit", "exit"):
            print("Exiting.")
            return
        if cmd in ("help", "h", "?"):
            print("""Commands:
 list                 - list python files in current directory
 select <num|name>    - select file by number (from list) or by path/name
 show                 - show header of selected file
 edit                 - interactive edit of selected file header (uses $EDITOR if set)
 add                  - add default header to selected file (will not overwrite existing keys)
 remove               - remove header from selected file
 bump [part]          - bump version of selected file (part=major|minor|patch)
 bumpall [part] [p]   - bump version for all python files under path (default cwd) (dry-run option applied)
 recurse <path>       - apply default headers to all python files under path (recursive)
 dryrun recurse <p>   - preview recursive application under path without writing
 refresh              - refresh file list in current directory
 ls                   - alias for list
 help                 - this help
 quit                 - exit
""")
            continue

        if cmd in ("list", "ls"):
            files = find_python_files(cwd, recurse=False)
            if not files:
                print("No python files found in current directory.")
                continue
            for i, f in enumerate(files, 1):
                print(f"{i:3d}. {os.path.basename(f)}  ({f})")
            continue

        if cmd == "refresh":
            files = find_python_files(cwd, recurse=False)
            print("Refreshed.")
            continue

        if cmd == "select":
            if not args:
                print("Provide number or filename.")
                continue
            token = args[0]
            try:
                idx = int(token)
                if 1 <= idx <= len(files):
                    selected = files[idx - 1]
                    print(f"Selected {selected}")
                else:
                    print("Index out of range.")
                continue
            except ValueError:
                cand = os.path.abspath(token)
                if os.path.exists(cand) and cand.endswith(".py"):
                    selected = cand
                    print(f"Selected {selected}")
                else:
                    matches = [f for f in files if os.path.basename(f) == token]
                    if len(matches) == 1:
                        selected = matches[0]
                        print(f"Selected {selected}")
                    elif len(matches) > 1:
                        print("Multiple matches, specify path or choose index:")
                        for i, f in enumerate(matches, 1):
                            print(f"{i:2d}. {f}")
                    else:
                        print("No match found.")
                continue

        if cmd == "show":
            if not selected:
                print("No file selected.")
                continue
            show_header_on_stdout(selected)
            continue

        if cmd == "edit":
            if not selected:
                print("No file selected.")
                continue
            interactive_edit_header(selected)
            continue

        if cmd == "add":
            if not selected:
                print("No file selected.")
                continue
            did = add_default_header_to_file(selected)
            print("Defaults added where missing." if did else "No changes necessary.")
            continue

        if cmd == "remove":
            if not selected:
                print("No file selected.")
                continue
            remove_header_from_file(selected)
            print("Header removed.")
            continue

        if cmd == "bump":
            if not selected:
                print("No file selected.")
                continue
            if not args:
                part = input("Which part to bump? (major/minor/patch): ").strip().lower()
            else:
                part = args[0].lower()
            if part not in ("major", "minor", "patch"):
                print("Invalid part.")
                continue
            if bump_version_in_file(selected, part):
                print("Bumped.")
            else:
                print("Failed to bump.")
            continue

        if cmd == "bumpall":
            part = args[0] if args else input("Which part to bump? (major/minor/patch): ").strip().lower()
            path = args[1] if len(args) > 1 else "."
            dry = "--dry-run" in args or "dry-run" in args
            changes = bump_version_in_tree(path, part, dry_run=dry)
            if dry:
                print("Dry-run. Changes that would be made:")
            for c in changes:
                print(c)
            print(f"{len(changes)} file(s) affected.")
            continue

        if cmd == "recurse":
            start = args[0] if args else "."
            dry = False
            if len(args) > 1 and args[1] == "--dry-run":
                dry = True
            changes = apply_defaults_recursively(start, dry_run=dry)
            if dry:
                print("Dry-run. Files that would be changed:")
            for c in changes:
                print(c)
            print(f"{len(changes)} file(s) {'would be changed' if dry else 'changed'}.")
            continue

        if cmd == "dryrun" and len(args) >= 1 and args[0] == "recurse":
            start = args[1] if len(args) > 1 else "."
            changes = apply_defaults_recursively(start, dry_run=True)
            print("Dry-run. Files that would be changed:")
            for c in changes:
                print(c)
            print(f"{len(changes)} file(s) would be changed.")
            continue

        print("Unknown command. Type 'help' for commands.")