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

    @transaction.atomic
    def handle(self, *args, **options):
        files_to_process = self.determine_files_to_process(
            options["paths"], pattern=options["pattern"]
        )

        limit = options.get("limit", None)
        if limit is not None:
            files_to_process = self.determine_records_to_process(
                files_to_process, limit=limit
            )

        eci = ExcelCollectionImporter(
            paths=files_to_process,
            durable=options["durable"],
            threshold=options["threshold"],
            preprocess=not bool(options["no_preprocess"]),
        )
        file_import_attempt = eci.process()

        eci.report.process()
        if options["dry_run"]:
            transaction.set_rollback(True)
            tqdm.write("DRY RUN; rolling back changes")
