import re
from pathlib import Path
from pyhead_tui import load_header_from_file, parse_header

def test_defaults_added_when_missing(tmp_path):
    # Create a python file with no header
    f = tmp_path / "simple.py"
    f.write_text("print('hello')\n", encoding="utf-8")

    state = load_header_from_file(str(f))
    tags = state["tags"]

    # Normalized keys (default transform = snake)
    assert "file" in tags
    assert tags["file"][0] == "simple.py"

    assert "mission" in tags
    assert tags["mission"][0] == "tbd."

    assert "status" in tags
    assert tags["status"][0] == "tbd."

    assert "notes" in tags
    assert tags["notes"][0] == "tbd."

    assert "version" in tags
    assert tags["version"][0] == "0.0.0"

    assert "date" in tags
    # DATE should look like YYYY-MM-DD HH:MM:SS
    assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", tags["date"][0])

def test_date_always_updated(tmp_path):
    f = tmp_path / "dated.py"
    # create a file with an old DATE in header
    content = [
        "# :date\n",
        "# 2000-01-01 00:00:00\n",
        "print('ok')\n",
    ]
    f.write_text("".join(content), encoding="utf-8")

    state = load_header_from_file(str(f))
    tags = state["tags"]

    assert "date" in tags
    assert tags["date"][0] != "2000-01-01 00:00:00"
    # still in expected datetime format
    assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", tags["date"][0])

def test_defaults_do_not_override_existing(tmp_path):
    f = tmp_path / "withtags.py"
    # Create a header that already contains VERSION and MISSION
    content = [
        "# :version\n",
        "# 1.2.3\n",
        "# :mission\n",
        "# Save the world\n",
        "print('ok')\n",
    ]
    f.write_text("".join(content), encoding="utf-8")

    state = load_header_from_file(str(f))
    tags = state["tags"]

    # Existing values should be preserved (except DATE which is updated)
    assert "version" in tags
    assert tags["version"][0] == "1.2.3"
    assert "mission" in tags
    assert tags["mission"][0] == "Save the world"
    assert "date" in tags
    assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", tags["date"][0])