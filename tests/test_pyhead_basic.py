from pyhead_tui import parse_header

def test_parse_header_basic():
    lines = [
        "#!/usr/bin/env python\n",
        "# Preamble line\n",
        "# :author\n",
        "# Alice <alice@example.com>\n",
        "print('hello')\n",
    ]
    shebang, header_end, preamble, tags = parse_header(lines)
    assert shebang == "#!/usr/bin/env python"
    assert header_end == 4
    assert preamble == ["Preamble line"]
    assert "author" in tags
    assert tags["author"] == ["Alice <alice@example.com>"]