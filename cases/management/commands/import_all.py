import json
import os
from pathlib import Path

from django.core.management import call_command
from django.db import transaction

from tqdm import tqdm
from django_import_data import BaseImportCommand


SCRIPT_DIR = Path(__file__).resolve().parent


class Command(BaseImportCommand):
    help = "Import all NRQZ data"

    PROGRESS_TYPE = None

    def add_arguments(self, parser):
        self.add_core_arguments(parser)
        parser.add_argument(
            "-c",
            "--commands",
            nargs="+",
            help="Specify a subset of commands (from importer_spec.json) to be executed",
        )
        parser.add_argument(
            "--preview",
            action="store_true",
            help="Don't execute any commands, just show what commands WILL executed",
        )
        parser.add_argument(
            "-I",
            "--importer-spec",
            help="The path to an 'importer specification' file. "
            "This maps importer (management command) name to its arguments "
            "(primarily path, though others also work)",
            default=os.path.join(SCRIPT_DIR, "importer_spec.json"),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        with open(options.pop("importer_spec")) as file:
            command_info = json.load(file)

        preview = options.pop("preview")
        commands = options.pop("commands")
        if commands:
            command_info = {
                command: info
                for command, info in command_info.items()
                if command in commands
            }
            if not command_info:
                raise ValueError(
                    f"Given commands ({commands}) did not yield any actual "
                    "subcommands! Check your spelling, etc., and try again"
                )
        if preview:
            tqdm.write("The following commands would have been executed:")

        for command, command_args in tqdm(
            command_info.items(), unit="importers", desc="Overall Progress"
        ):
            tqdm.write(f"--- {command} ---")
            paths = command_args.pop("paths")
            sub_options = {
                **command_args,
                # TODO: Would be nice to fix this; duplicated
                # **options
                **{
                    option: options[option]
                    for option in ["limit", "rows", "overwrite", "dry_run"]
                    if option in options
                },
            }
            if preview:
                tqdm.write(f"call_command({command!r}, *{paths!r}, **{sub_options!r})")
            else:
                call_command(command, *paths, **sub_options)
            tqdm.write(f"--- DONE ---")
