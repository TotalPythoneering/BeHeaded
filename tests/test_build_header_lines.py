from collections import OrderedDict
from pyhead_tui import build_header_lines, parse_header


def test_build_header_lines_creates_comment_header_and_roundtrips():
    shebang = "#!/usr/bin/env python"
    preamble = ["Preamble A", "Preamble B"]
    tags = OrderedDict()
    tags["notes"] = ["first", "second: still first"]
    tags["author_name"] = ["Alice"]

    header_lines = build_header_lines(shebang, preamble, tags)
    # header_lines should be a list of strings ending with at least a blank line
    assert isinstance(header_lines, list)
    assert any(line.startswith("# :notes") for line in header_lines)
    # append a simple body and re-parse
    full_lines = header_lines + ["print('ok')\n"]
    shebang2, header_end2, preamble2, tags2 = parse_header(full_lines)
    assert shebang2 == shebang
    # preamble should match (order preserved)
    assert preamble2 == preamble
    # tags and their values should roundtrip
    assert "notes" in tags2
    assert tags2["notes"][0] == "first"
    assert tags2["notes"][1] == "second: still first"
    assert "author_name" in tags2
    assert tags2["author_name"] == ["Alice"]


def test_build_header_lines_single_blank_line_separator():
    shebang = None
    preamble = []
    tags = OrderedDict()
    tags["one"] = ["v1"]
    header_lines = build_header_lines(shebang, preamble, tags)
    joined = "".join(header_lines)
    # There should be at most two consecutive newlines in the header area (i.e., no triple-newline)
    assert "\n\n\n" not in joined
    # ensure the header ends with a blank line (separator)
    assert joined.endswith("\n\n")