"""Run all importers in the given .spec file"""

from tqdm import tqdm


from django.core.management import call_command
from django.db import transaction


from django_import_data.models import ModelImporter

from cases.models import CaseGroup
from ._base_meta_import import BaseMetaImportCommand


class Command(BaseMetaImportCommand):
    help = "Import all NRQZ data"

    PROGRESS_TYPE = None

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--preview",
            action="store_true",
            help="Don't execute any commands, just show what commands WILL executed",
        )

    def handle_subcommands(self, command_info, preview, **options):
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
                    for option in [
                        "limit",
                        "rows",
                        "overwrite",
                        "skip",
                        "dry_run",
                        "no_transaction",
                        "start_index",
                        "end_index",
                        "verbosity",
                    ]
                    if option in options
                },
            }
            if preview:
                tqdm.write(f"call_command({command!r}, *{paths!r}, **{sub_options!r})")
            else:
                call_command(command, *paths, **sub_options)

    def handle(self, *args, **options):
        command_info = self.handle_importer_spec(
            import_spec_path=options.pop("importer_spec"),
            requested_commands=options.pop("commands"),
        )
        preview = options.pop("preview")
        if preview:
            tqdm.write("The following commands would have been executed:")

        # If user has turned off transaction, then don't open one. Also
        # pass the option through to the subcommand(s) so that they don't
        # open one either
        if options["no_transaction"]:
            self.handle_subcommands(command_info, preview, **options)
        # If the user has not turned of transaction, then DO open one
        else:
            with transaction.atomic():
                # Note that we have to pass the no_transaction option through manually
                # to avoid subcommands from creating their own
                self.handle_subcommands(
                    command_info, preview, **{**options, "no_transaction": True}
                )

                # Handle rollback here, since subcommands won't be doing it
                if options["dry_run"]:
                    transaction.set_rollback(True)
                    tqdm.write("DRY RUN; rolling back changes")

        self.post_import_actions()
        tqdm.write(f"--- DONE ---")

    def post_import_actions(self):
        # Build case groups
        CaseGroup.objects.build_all_case_groups()
        # Derive appropriate statuses for all MIs. This will also
        # propagate to all FIAs, FIs, and FIBs
        tqdm.write("Deriving status values for Model Importers")
        ModelImporter.objects.all().derive_values()
