from importlib import import_module
from pathlib import Path
import json
import os

from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType

from django_import_data.models import FileImportAttempt, RowData

from cases.models import Case

SCRIPT_DIR = Path(__file__).resolve().parent


def get_example_data(file_import_attempts, unmapped_header):
    path = None
    nrqz_id = None
    example_data = None
    # First, assume that the data was able to be stored in a sensible way (that is,
    # it could be represented as a dict and stored straight into RowData.data)
    row_datas = RowData.objects.filter(
        # data should have the key of the unmapped header
        data__has_key=unmapped_header,
        # and the RowData should be linked to one of the FIAs we were given
        # (don't want to return example data from the wrong file!)
        model_import_attempts__file_import_attempt__id__in=file_import_attempts,
    )
    # If this worked, we go through every row_data looking for one with a
    # non-null value for our unmapped header
    if row_datas:
        for row_data in row_datas:
            example_data = row_data.data[unmapped_header]
            # If the value is not null, make sure it isn't a 0, either!
            if example_data:
                try:
                    foo = int(example_data)
                except ValueError:
                    pass
                else:
                    if foo != 0:
                        # path = row_data.file_import_attempt.imported_from
                        case = Case.objects.filter(
                            model_import_attempt__row_data=row_data
                        ).first()

                        if case:
                            nrqz_id = case.case_num
                            break
    # If that didn't work, assume we are dealing with the NAM stuff, which
    # has duplicate keys in its data and thus can't be stored as a dict
    else:
        # However, it does store a unique list of headers! So we can use this
        # to get all of the row_datas that could possibly have a value for
        # our unmapped header
        row_datas = RowData.objects.filter(
            headers__has_key=unmapped_header,
            model_import_attempts__file_import_attempt__id__in=file_import_attempts,
        )

        for row_data in row_datas:
            # First check the main dict (non-facility info) for example_data
            try:
                example_data = row_data.data["main_dict"][unmapped_header]
            except KeyError:
                # If that doesn't work, check all of its facility dicts
                for facility_dict in row_data.data["facility_dicts"]:
                    try:
                        example_data = facility_dict[unmapped_header]
                    except KeyError:
                        pass
                    # Check that example data is non-zero, if it exists
                    if example_data:
                        try:
                            foo = int(example_data)
                        except ValueError:
                            pass
                        else:
                            if foo != 0:
                                break
            else:
                # Check that example data is non-zero, if it exists
                if example_data:
                    try:
                        foo = int(example_data)
                    except ValueError:
                        pass
                    else:
                        if foo != 0:
                            break

            if example_data:
                path = row_data.file_import_attempt.imported_from
                nrqz_id = row_data.data["main_dict"]["nrqzID"]
                break

    return example_data, path, nrqz_id


class Command(BaseCommand):
    def add_arguments(self, parser):

        parser.add_argument(
            "-I",
            "--importer-spec",
            help="The path to an 'importer specification' file. "
            "This maps importer (management command) name to its arguments "
            "(primarily path, though others also work)",
            default=os.path.join(SCRIPT_DIR, "importer_spec.json"),
        )

    def handle(self, *args, **options):
        with open(options.pop("importer_spec")) as file:
            command_info = json.load(file)

        form_maps_by_importer = {
            name: {
                "form_maps": import_module(
                    f"cases.management.commands.{name}"
                ).Command.FORM_MAPS,
                "path": command_info[name]["paths"][0],
            }
            for name in command_info
        }

        for importer_name, importer_info in form_maps_by_importer.items():
            importer_form_maps = importer_info["form_maps"]
            print(importer_name)
            for form_map in importer_form_maps:
                form_map.explain()

            fias_for_path = FileImportAttempt.objects.filter(
                imported_from__startswith=importer_info["path"]
            )
            unmapped_headers = fias_for_path.values_list(
                "errors__header_checks__unmapped_headers", flat=True
            )
            if not all(unmapped_headers):
                unmapped_headers = fias_for_path.values_list(
                    "errors__unmapped_headers", flat=True
                )

            if all(unmapped_headers):
                unmapped_headers = sorted(
                    {unmapped_header for L in unmapped_headers for unmapped_header in L}
                )
            else:
                unmapped_headers = None

            if unmapped_headers:
                print("Unmapped headers (format is <header_name>: <example_value>):")
                for unmapped_header in unmapped_headers:
                    example_data, path, nrqz_id = get_example_data(
                        fias_for_path, unmapped_header
                    )

                    explanation_str = f"  * {unmapped_header}: {example_data.strip()}"
                    assert not (example_data is path is nrqz_id is None), "hmmm"
                    if nrqz_id:
                        explanation_str += f" [for nrqz ID: {nrqz_id}]"

                    # if path:
                    #     explanation_str += f" (from: {path})"
                    print(explanation_str)

            else:
                print("  No unmapped headers!")

            print("=" * 80)
