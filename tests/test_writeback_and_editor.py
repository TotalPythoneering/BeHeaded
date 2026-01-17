import stat
from pathlib import Path
from pyhead_tui import load_header_from_file, write_back, edit_tag_via_editor, parse_header

def _make_sample_file(path: Path, author="Alice"):
    content = [
        "#!/usr/bin/env python\n",
        "# Preamble text\n",
        "# :author\n",
        f"# {author}\n",
        "\n",
        "def main():\n",
        "    print('hello')\n",
    ]
    path.write_text("".join(content), encoding="utf-8")
    return content

def test_write_back_updates_author(tmp_path):
    f = tmp_path / "sample.py"
    _make_sample_file(f, author="Alice")
    state = load_header_from_file(str(f))
    # update in-memory tag
    state["tags"]["author"] = ["Bob <bob@example.com>"]
    write_back(state)

    # File should be updated and a backup created
    text = f.read_text(encoding="utf-8")
    assert "# :author" in text
    assert "# Bob <bob@example.com>" in text

    bak = str(f) + ".bak"
    assert Path(bak).exists()
    # backup should contain original author
    bak_text = Path(bak).read_text(encoding="utf-8")
    assert "Alice" in bak_text

def test_edit_tag_via_editor_creates_and_updates(tmp_path, monkeypatch):
    f = tmp_path / "sample2.py"
    _make_sample_file(f, author="Original")

    state = load_header_from_file(str(f))

    # Create a tiny editor script that writes new contents to the provided filename argument
    editor_script = tmp_path / "fake_editor.sh"
    editor_script.write_text("#!/usr/bin/env sh\nprintf '%s\n' 'Edited line one' > \"$1\"\nexit 0\n", encoding="utf-8")
    # make it executable
    editor_script.chmod(editor_script.stat().st_mode | stat.S_IXUSR)

    monkeypatch.setenv("EDITOR", str(editor_script))

    # Update existing tag
    edit_tag_via_editor(state, "author")
    assert state["tags"]["author"] == ["Edited line one"]

    # Create a new tag via editor
    edit_tag_via_editor(state, "notes")
    assert state["tags"]["notes"] == ["Edited line one"]

def test_parse_header_preserves_behavior():
    # sanity test that parse_header still returns expected structure
    lines = [
        "#!/usr/bin/env python\n",
        "# Start\n",
        "# :tag\n",
        "# val\n",
        "print('x')\n",
    ]
    shebang, header_end, preamble, tags = parse_header(lines)
    assert shebang == "#!/usr/bin/env python"
    assert header_end == 4
    assert preamble == ["Start"]
    assert tags["tag"] == ["val"]