# MISSION: Packaging, tagging & testing support.
# STATUS: Research
# VERSION: 0.0.2
# NOTES: Use the basics.
# DATE: 2026-01-18 06:53:06
# FILE: __init__.py
# AUTHOR: Randall Nagy
#
"""
BeHeaded package init - re-export core symbols.

This file keeps the public API small and stable for tests and users.
"""
from .core import (  # noqa: F401
    read_file_header,
    write_header_to_file,
    add_default_header_to_file,
    read_bejson_for_folder,
    get_wrap_width_from_defaults,
    file_mtime_string,
    bump_version_in_file,
    bump_version_in_tree,
    apply_defaults_recursively,
    cli_main,
    mainloop,
)

from .tag_manager import TagManager

__all__ = [
    "read_file_header",
    "write_header_to_file",
    "add_default_header_to_file",
    "read_bejson_for_folder",
    "get_wrap_width_from_defaults",
    "file_mtime_string",
    "bump_version_in_file",
    "bump_version_in_tree",
    "apply_defaults_recursively",
    "cli_main",
    "mainloop",
    "TagManager"
]

