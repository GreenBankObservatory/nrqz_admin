"""Spec-file-related functions/utilities"""

import os
from pathlib import Path
import json
import re

# TODO: Naughty! Fix this... one day...
SCRIPT_DIR = Path(__file__).resolve().parent
SPEC_FILE = os.path.join(
    SCRIPT_DIR.parent, "cases", "management", "commands", "importer_spec.json"
)


def load_spec(import_spec_path):
    with open(import_spec_path) as file:
        return json.load(file)


def parse_importer_spec(import_spec_path, requested_commands=None):
    command_info = load_spec(import_spec_path)

    if requested_commands:
        command_info = {
            command_from_file: info
            for command_from_file, info in command_info.items()
            if any(
                requested_command in command_from_file
                for requested_command in requested_commands
            )
        }
        if not command_info:
            raise ValueError(
                f"Given commands ({requested_commands}) did not yield any actual "
                "subcommands! Check your spelling, etc., and try again"
            )

    return command_info


def determine_importer_from_path(path, import_spec_path=None):
    if import_spec_path is None:
        import_spec_path = SPEC_FILE
    command_info = load_spec(import_spec_path)

    known_patterns = set()
    for importer_name, info in command_info.items():
        pattern = info.get("pattern", None)
        if pattern:
            known_patterns.add(pattern)
            if re.match(pattern, path):
                return importer_name

    # If we get here, it means that none of the patterns defined in our .spec
    # file matched the given path. So, we can't guess this, and the user
    # will need to do it by hand
    raise ValueError(
        f"No patterns match file {os.path.basename(path)!r}! You will need to "
        "specify the importer manually"
    )
