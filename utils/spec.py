"""Spec-file-related functions/utilities"""

import os
from pathlib import Path
import json
import re

# TODO: Naughty! Fix this... one day...
SCRIPT_DIR = Path(__file__).resolve().parent
SPEC_FILE = os.path.join(
    SCRIPT_DIR.parent, "cases", "management", "commands", "importer_spec2.json"
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


def determine_importer_from_path(path, import_spec_path):
    command_info = load_spec(import_spec_path)

    for importer_name, info in command_info.items():
        if re.match(info["pattern"], path):
            return importer_name

    return None
