import os
from pathlib import Path
from pyhead_tui import load_header_from_file, write_back, parse_header


def _make_demo_file(path: Path):
    content = [
        "#!/usr/bin/env python\n",
        "# Demo preamble line\n",
        "# :Author Name\n",
        "# Original Author <orig@example.com>\n",
        "# Title: Demo: a title with colon\n",
        "# Notes: line one\n",
        "# line two\n",
        "\n",
        "def greet():\n",
        "    print('hello world')\n",
    ]
    path.write_text("".join(content), encoding="utf-8")
    return content


def test_write_back_preserves_shebang_and_body(tmp_path):
    f = tmp_path / "demo_preserve.py"
    _make_demo_file(f)
    state = load_header_from_file(str(f))

    # modify a tag in memory and write back
    state["tags"]["author_name"] = ["Updated Author <updated@example.com>"]
    write_back(state)

    text = f.read_text(encoding="utf-8")
    # shebang should still be present at the very top
    assert text.startswith("#!/usr/bin/env python")
    # the body of the file (function greet) should still be present
    assert "def greet():" in text
    # backup file should exist and contain the original author
    bak = str(f) + ".bak"
    assert Path(bak).exists()
    bak_text = Path(bak).read_text(encoding="utf-8")
    assert "Original Author" in bak_text


def test_write_back_uses_normalized_marker_and_no_triple_blank_lines(tmp_path):
    f = tmp_path / "demo_normalize.py"
    _make_demo_file(f)
    state = load_header_from_file(str(f))

    # set a normalized key (default normalization is snake_case -> author_name)
    state["tags"]["author_name"] = ["Normalized Author <norm@example.com>"]
    write_back(state)

    text = f.read_text(encoding="utf-8")
    # the writer should produce a normalized marker line using the normalized tag key
    assert "# :author_name" in text
    # ensure we don't produce triple newlines; at worst we should have single blank-line separation
    assert "\n\n\n" not in text


def test_parse_header_roundtrip_after_write_back(tmp_path):
    f = tmp_path / "demo_roundtrip.py"
    _make_demo_file(f)
    state = load_header_from_file(str(f))

    # change several tags and write back
    state["tags"]["author_name"] = ["Roundtrip Author"]
    state["tags"]["title"] = ["Roundtrip Title"]
    write_back(state)

    # re-parse using parse_header and check tags exist
    shebang, header_end, preamble, tags = parse_header(f.read_text(encoding="utf-8").splitlines(True))
    assert "author_name" in tags
    assert tags["author_name"][0] == "Roundtrip Author"
    assert "title" in tags
    assert "Demo preamble line" in preamble[0] or "Demo preamble line" in preamble

