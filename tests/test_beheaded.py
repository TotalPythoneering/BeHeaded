# MISSION: Support the testing of the BeHeaded package.
# STATUS: Production
# VERSION: 1.0.0
# NOTES: Pytest test cases.
# Both pytest and BeHeaded must be installed for these tests to work properly.
# Place this file in the tests/ directory so pytest will pick it up automatically.
# DATE: 2026-01-18 03:59:42
# FILE: test_beheaded.py
# AUTHOR: Randall Nagy
#
import os
import json
import textwrap
from beheaded import (
    read_file_header,
    write_header_to_file,
    add_default_header_to_file,
    read_bejson_for_folder,
    get_wrap_width_from_defaults,
    file_mtime_string,
    bump_version_in_file,
    bump_version_in_tree,
    apply_defaults_recursively,
)

def make_temp_py(content: str, dirpath: str, name: str = "script.py") -> str:
    path = os.path.join(dirpath, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path

def test_parse_and_write_roundtrip(tmp_path):
    src = textwrap.dedent("""\
    # MISSION: Do the thing
    # NOTES: initial note
    #
    # AUTHOR: Alice
    print("hello")
    """)
    p = make_temp_py(src, str(tmp_path), "a.py")
    shebang, header, rest = read_file_header(p)
    assert header.get("MISSION").startswith("Do the thing")
    # write back using defaults (this will also ensure FILE: is written)
    write_header_to_file(p, shebang, header, {})
    with open(p, "r", encoding="utf-8") as fh:
        out = fh.read()
    assert "MISSION:" in out
    assert "AUTHOR:" in out
    assert 'print("hello")' in out
    # FILE: must equal the base filename
    shebang2, header2, rest2 = read_file_header(p)
    assert header2.get("FILE") == os.path.basename(p)

def test_bejson_defaults_and_wrap(tmp_path):
    folder = str(tmp_path)
    bejson = {"AUTHOR": "Tester", "WRAP_WIDTH": 30}
    with open(os.path.join(folder, ".BeHeaders.json"), "w", encoding="utf-8") as fh:
        json.dump(bejson, fh)
    p = make_temp_py("print('x')\n", folder, "b.py")
    changed = add_default_header_to_file(p)
    assert changed is True
    # read header and ensure the AUTHOR default applied and FILE is set
    _, header, _ = read_file_header(p)
    assert header.get("AUTHOR") == "Tester"
    assert header.get("FILE") == os.path.basename(p)
    wd = get_wrap_width_from_defaults(read_bejson_for_folder(folder))
    assert wd == 30

def test_bump_version(tmp_path):
    folder = str(tmp_path)
    p = make_temp_py("# VERSION: 0.1.2\nprint('x')\n", folder, "c.py")
    ok = bump_version_in_file(p, "patch")
    assert ok
    _, header, _ = read_file_header(p)
    assert header.get("VERSION") == "0.1.3"
    assert header.get("FILE") == os.path.basename(p)

def test_bump_version_tree(tmp_path):
    folder = str(tmp_path)
    p1 = make_temp_py("# VERSION: 0.0.0\n", folder, "d1.py")
    p2 = make_temp_py("print('no version')\n", folder, "d2.py")
    changed = bump_version_in_tree(folder, "patch", dry_run=True)
    assert any("d1.py" in c for c in changed)
    assert any("d2.py" in c for c in changed)

def test_apply_defaults_recursively(tmp_path):
    folder = str(tmp_path)
    p1 = make_temp_py("print('x')\n", folder, "e1.py")
    changed = apply_defaults_recursively(folder, dry_run=True)
    assert any("e1.py" in c for c in changed)
