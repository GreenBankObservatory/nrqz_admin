"""Import Excel Technical Data"""

import os
import re

from importers.excel.excel_importer import (
    ExcelCollectionImporter,
    DEFAULT_THRESHOLD,
    DEFAULT_PREPROCESS,
)
from django_import_data import BaseImportCommand


# TODO: MOVE
def determine_files_to_process(paths, pattern=r".*\.(xls.?|csv)$"):
    files = []
    for path in paths:
        if os.path.isfile(path):
            files.append(path)
        elif os.path.isdir(path):
            files.extend(
                [
                    os.path.join(path, file)
                    for file in os.listdir(path)
                    if re.search(pattern, file)
                ]
            )
        else:
            raise ValueError(f"Given path {path!r} is not a directory or file!")

    return sorted(files)


class Command(BaseImportCommand):
    help = "Import Excel Technical Data"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "-i",
            "--interactive",
            action="store_true",
            help="If given, drop into an interactive shell upon unhandled exception",
        )

        parser.add_argument(
            "-p",
            "--pattern",
            default=r".*\.(xls.?|csv)$",
            help=(
                "Regular expression used to identify Excel application files. "
                "Used only when a directory is given in path"
            ),
        )
        parser.add_argument(
            "-t",
            "--threshold",
            type=float,
            default=DEFAULT_THRESHOLD,
            help="Threshold of invalid headers which constitute an invalid sheet.",
        )
        parser.add_argument(
            "--no-preprocess",
            default=not DEFAULT_PREPROCESS,
            action="store_true",
            help="Indicate that no pre-processing needs to be done on the given input file(s)",
        )

    def handle(self, *args, **options):
        files_to_process = determine_files_to_process(
            [options["path"]], pattern=options["pattern"]
        )

        limit = options.get("limit", None)
        if limit is not None:
            files_to_process = self.get_random_rows(files_to_process, limit)

        eci = ExcelCollectionImporter(
            paths=files_to_process,
            durable=options["durable"],
            threshold=options["threshold"],
            preprocess=not bool(options["no_preprocess"]),
        )
        eci.process()

        eci.report.process()
