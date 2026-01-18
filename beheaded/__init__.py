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
]