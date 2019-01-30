"""Import Excel Technical Data"""

from tqdm import tqdm

from django.db import transaction

from django_import_data import BaseImportCommand

from importers.excel.excel_importer import (
    ExcelCollectionImporter,
    DEFAULT_THRESHOLD,
    DEFAULT_PREPROCESS,
)


class Command(BaseImportCommand):
    help = "Import Excel Technical Data"

    PROGRESS_TYPE = BaseImportCommand.PROGRESS_TYPES.FILE

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "-i",
            "--interactive",
            action="store_true",
            help="If given, drop into an interactive shell upon unhandled exception",
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

    def handle_files(self, files_to_process, **options):
        eci = ExcelCollectionImporter(
            paths=files_to_process,
            durable=options["durable"],
            threshold=options["threshold"],
            preprocess=not bool(options["no_preprocess"]),
        )
        file_import_attempt = eci.process()
