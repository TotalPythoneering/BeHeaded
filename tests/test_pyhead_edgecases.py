from pyhead_tui import parse_header
import os

def test_no_header():
    lines = [
        "print('no header')\n",
        "x = 1\n",
    ]
    shebang, header_end, preamble, tags = parse_header(lines)
    assert shebang is None
    assert header_end == 0
    assert preamble == []
    assert tags == {}

def test_shebang_only():
    lines = [
        "#!/usr/bin/env python\n",
        "print('hello')\n",
    ]
    shebang, header_end, preamble, tags = parse_header(lines)
    assert shebang == "#!/usr/bin/env python"
    assert header_end == 1
    assert preamble == []
    assert tags == {}

def test_preamble_only():
    lines = [
        "# Preamble a\n",
        "# Preamble b\n",
        "def f(): pass\n",
    ]
    shebang, header_end, preamble, tags = parse_header(lines)
    assert shebang is None
    assert header_end == 2
    assert preamble == ["Preamble a", "Preamble b"]
    assert tags == {}

def test_empty_tag_marker_ignored():
    lines = [
        "# :\n",
        "# :author\n",
        "# Name\n",
        "x=1\n",
    ]
    shebang, header_end, preamble, tags = parse_header(lines)
    assert "author" in tags
    assert tags["author"] == ["Name"]

def test_multiple_values_for_tag():
    lines = [
        "# :notes\n",
        "# Line one\n",
        "# Line two\n",
        "# :author\n",
        "# A Person\n",
        "print('ok')\n",
    ]
    shebang, header_end, preamble, tags = parse_header(lines)
    assert "notes" in tags
    assert tags["notes"] == ["Line one", "Line two"]
    assert tags["author"] == ["A Person"]

def test_tag_with_value_on_same_line():
    lines = [
        "#!/usr/bin/env python\n",
        "# Some preamble\n",
        "# Author: Alice <alice@example.com>\n",
        "print('done')\n",
    ]
    shebang, header_end, preamble, tags = parse_header(lines)
    assert shebang == "#!/usr/bin/env python"
    assert header_end == 3
    assert preamble == ["Some preamble"]
    assert "author" in tags
    assert tags["author"] == ["Alice <alice@example.com>"]

def test_title_with_colon_in_value():
    lines = [
        "# Title: A long: value with colon\n",
        "# More value\n",
        "x=1\n",
    ]
    shebang, header_end, preamble, tags = parse_header(lines)
    assert "title" in tags
    assert tags["title"][0] == "A long: value with colon"
    assert tags["title"][1] == "More value"

def test_colon_style_with_spaces_and_no_value():
    lines = [
        "# :Author Name\n",
        "# Extra line\n",
        "y=2\n",
    ]
    shebang, header_end, preamble, tags = parse_header(lines)
    # default normalization -> snake_case
    assert "author_name" in tags
    assert tags["author_name"] == ["Extra line"]

def test_normalization_preserve_env(monkeypatch):
    # set transform to preserve: keys should be exactly as provided (trimmed)
    monkeypatch.setenv("PYHEAD_TAG_TRANSFORM", "preserve")
    lines = [
        "# :Author Name\n",
        "# Value\n",
    ]
    shebang, header_end, preamble, tags = parse_header(lines)
    assert "Author Name" in tags
    assert tags["Author Name"] == ["Value"]
    # cleanup env var for other tests
    monkeypatch.delenv("PYHEAD_TAG_TRANSFORM", raising=False)