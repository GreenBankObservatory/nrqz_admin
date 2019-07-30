import json
import os
from pathlib import Path

from django_import_data import BaseImportCommand

SCRIPT_DIR = Path(__file__).resolve().parent


class BaseMetaImportCommand(BaseImportCommand):
    def add_arguments(self, parser):
        self.add_core_arguments(parser)
        parser.add_argument(
            "-c",
            "--commands",
            nargs="+",
            help="Specify a subset of commands (from importer_spec.json) to be executed",
        )
        parser.add_argument(
            "-I",
            "--importer-spec",
            help="The path to an 'importer specification' file. "
            "This maps importer (management command) name to its arguments "
            "(primarily path, though others also work)",
            default=os.path.join(SCRIPT_DIR, "importer_spec.json"),
        )

    def handle_importer_spec(self, import_spec_path, requested_commands):
        with open(import_spec_path) as file:
            command_info = json.load(file)

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
