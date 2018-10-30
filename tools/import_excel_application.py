#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Import Excel NRQZ application forms into the DB

Each Excel file creates a Batch. Each case number represents a Case.
Each data row in the Excel file creates a Facility.

Any files matching *.xls* or *.csv will be considered applications and
an attempt will be made to import them
"""

import argparse
from collections import namedtuple, OrderedDict
from itertools import chain
import json
import os
from pprint import pprint
import re
import sys
import traceback

import django
from django.db import transaction
from django.db import models

django.setup()

import pyexcel
from tqdm import tqdm

from cases.models import Attachment, Batch, Case, Facility
from tools.excelfieldmap import facility_field_map
from tools.import_report import ImportReport


INTERACTIVE = False


class ManualRollback(Exception):
    pass


def load_rows(path, import_reporter):
    sheet = pyexcel.get_sheet(file_name=path)

    return sheet.array


def derive_field_from_validation_error(tb):
    """Examine ValidationError traceback, derive triggering field"""

    # Get the last frame in the traceback (list of tuples)
    frame = list(traceback.walk_tb(tb))[-1][0]
    # If this frame contains a "self" object that is an instance of a Django Field...
    if "self" in frame.f_locals and isinstance(frame.f_locals["self"], models.Field):
        # ...then we can examine it to determine which field it is
        return frame.f_locals["self"]
    else:
        raise ValueError("Cannot derive field!")


def excepthook(type_, value, tb):
    if type_ == ManualRollback:
        return

    # Print the exception, as we would expect
    traceback.print_exception(type_, value, tb)
    # Then grab the last frame from it
    field = derive_field_from_validation_error(tb)
    if field:
        tqdm.write(f"Error ocurred in relation to field: {field}", file=sys.stderr)
    # Otherwise we might drop into an interactive shell...
    else:
        # ...if we have indicated we want to
        if INTERACTIVE:
            import ipdb

            ipdb.post_mortem(tb)


def indentify_invalid_rows(rows, threshold=None):
    if threshold is None:
        threshold = 0.7

    invalid_row_indices = []
    for ri, row in enumerate(rows):
        invalid_cells = 0
        for cell in row:
            if not str(cell):
                # tqdm.write(f"Found invalid cell: {cell!r}")
                invalid_cells += 1

        if invalid_cells / len(row) > threshold:
            tqdm.write(
                f"Found invalid row {ri} (>{threshold * 100}% cells invalid): {row}"
            )
            invalid_row_indices.append(ri)

    return invalid_row_indices


def gen_header_field_map(headers):
    header_field_map = OrderedDict(
        [(header, facility_field_map.get(header, None)) for header in headers]
    )
    return header_field_map


def create_facility_dict_from_row(header_field_map, row, import_reporter, row_num):

    facility_dict = {}
    for header, importer, cell in zip(
        header_field_map.keys(), header_field_map.values(), row
    ):
        if importer and importer.to_field:
            try:
                facility_dict[importer.to_field] = importer.converter(cell)
            except (ValueError) as error:
                import_reporter.add_row_error(
                    header,
                    row_num,
                    {
                        "converter": importer.converter.__name__,
                        "field": importer.to_field,
                        "error_type": "conversion",
                        "error": str(error),
                        "value": cell,
                    },
                )
        else:
            tqdm.write(
                "Either no field importer or no importer.to_field; skipping "
                f"value {cell!r} for header {header!r}!"
            )
            continue

    return facility_dict


SheetError = namedtuple("SheetError", ["type", "description"])
# HeaderError = namedtuple("")


def create_facility(header_field_map, facility_dict, case):
    try:
        facility = Facility(**facility_dict, case=case)
    except TypeError:
        pprint(facility_dict)
        raise
    try:
        with transaction.atomic():
            facility.save()
    except (django.core.exceptions.ValidationError, ValueError, TypeError) as error:
        field = derive_field_from_validation_error(error.__traceback__)
        field_header_map = {
            value.to_field: key
            for key, value in header_field_map.items()
            if value is not None
        }
        value = facility_dict[field.name]
        derived_header = field_header_map[field.name]
        error_ = (
            derived_header,
            {
                "converter": facility_field_map[derived_header].converter.__name__,
                "field": field.name,
                "error_type": "validation",
                "error": str(error.args),
                "value": str(value),
            },
        )
    else:
        error_ = None
        # tqdm.write(f"Created {facility}")

    return error_


# https://regex101.com/r/gRPTN8/1
nrqz_id_regex_str = r"^(?P<case_num>\d+)[\s_\*]+(?:\(.*\)[\s_]+)?(?P<site_name>(?:(?:\w+\s+)?\S{5}|\D+))[\s_]+(?P<facility_name>\S+)$"
nrqz_id_regex = re.compile(nrqz_id_regex_str)
nrqz_id_regex_fallback_str = r"^(?P<case_num>\d+).*"
nrqz_id_regex_fallback = re.compile(nrqz_id_regex_fallback_str)


def derive_case_num_from_nrqz_id(nrqz_id):
    try:
        match = nrqz_id_regex.match(nrqz_id)
    except TypeError:
        tqdm.write(f"nrqz_id: {nrqz_id!r}")
        raise

    if not match:
        match = nrqz_id_regex_fallback.match(nrqz_id)
        if not match:
            raise ValueError(
                f"Could not parse NRQZ ID '{nrqz_id}' using "
                f"'{nrqz_id_regex_str}' or '{nrqz_id_regex_fallback_str}'!"
            )
    return match["case_num"]


def create_case_map(header_field_map, data, nrqz_id_field, import_reporter):
    """Create map of { case_num: { row_num: facility_dict } } and return"""

    case_map = {}
    for row in data:
        # Pull out the row number from the row...
        row_num = row[-1]
        facility_dict = create_facility_dict_from_row(
            header_field_map, row, import_reporter, row_num
        )
        # Derive the case number from the NRQZ ID (or Site Name, if no NRQZ ID found earlier)
        try:
            case_num = derive_case_num_from_nrqz_id(str(facility_dict[nrqz_id_field]))
        except ValueError as error:
            # If there's an error...
            field_header_map = {
                value.to_field: key
                for key, value in header_field_map.items()
                if value is not None
            }
            header = field_header_map[nrqz_id_field]
            # ...consider it a "data" error and report it
            import_reporter.add_row_error(
                header, row_num, {"error": str(error), "converter": None, "value": None}
            )
        else:
            # If there's not an error, add the new facility_dict to our case_dict
            if case_num in case_map:
                case_map[case_num][row_num] = facility_dict
            else:
                case_map[case_num] = {row_num: facility_dict}

    return case_map


def get_duplicate_headers(header_field_map):
    to_fields = [
        importer.to_field for importer in header_field_map.values() if importer
    ]

    if len(set(to_fields)) != len(to_fields):
        dups = {}
        for header, importer in header_field_map.items():
            if importer and to_fields.count(importer.to_field) > 1:
                if importer.to_field in dups:
                    dups[importer.to_field].append(header)
                else:
                    dups[importer.to_field] = [header]

            # There are _a lot_ of sheets that use a blank header as the
            # comments column. Generally this is fine, but sometimes there
            # is an explicit comments header _and_ a blank header. Since these
            # both map to the comments field, we need to reconcile this somehow
            # to avoid duplicate detection from being triggered.
            # So: If we have detected duplicates in the comments field, AND
            # a blank header is one of the duplicates...
            if "comments" in dups and "" in dups["comments"]:
                # ...remove it from the comments
                dups["comments"].remove("")

        return dups
    else:
        return None


def derive_nrqz_id_field(header_field_map):
    to_fields = [fm.to_field for fm in header_field_map.values() if fm]
    nrqz_id_fields = ["nrqz_id", "site_name"]
    for nrqz_id_field in nrqz_id_fields:
        if nrqz_id_field in to_fields:
            return nrqz_id_field

    return None


def get_unmapped_headers(header_field_map):
    return [header for header, field in header_field_map.items() if field is None]


@transaction.atomic
def process_excel_file(excel_path, threshold=None):
    """Create objects from given path"""

    import_reporter = ImportReport(excel_path)

    # A Batch representing this Excel file
    batch = Batch.objects.create(
        name=os.path.basename(excel_path), comments=f"Created by {__file__}"
    )

    # An attachment referencing the original Excel (or .csv) file
    batch.attachments.add(
        Attachment.objects.create(path=excel_path, comments=f"Attached by {__file__}")
    )

    rows = load_rows(excel_path, import_reporter)
    # A list of the headers actually in the file
    headers = rows[0][:-1]
    # A list of rows containing data
    data = rows[1:]
    # Generate a map of headers to field importers
    header_field_map = gen_header_field_map(headers)
    # If multiple headers map to the same field, report this as an error
    duplicate_headers = get_duplicate_headers(header_field_map)
    if duplicate_headers:
        import_reporter.set_duplicate_headers(duplicate_headers)

    # If some headers don't map to anything, report this as an error
    unmapped_headers = get_unmapped_headers(header_field_map)
    if unmapped_headers:
        import_reporter.set_unmapped_headers(unmapped_headers)

    # Determine the field in which our NRQZ ID string has been stored
    # This will be used later to parse out the case number
    nrqz_id_field = derive_nrqz_id_field(header_field_map)
    # If we can't find it, add an error
    if not nrqz_id_field:
        import_reporter.add_sheet_error(
            {
                "error_type": "nrqz_id_header_not_found",
                "error": "No NRQZ ID header found; tried site_name and nrqz_id",
            }
        )
    else:
        # Create our case->row_num->facility map
        case_map = create_case_map(
            header_field_map, data, nrqz_id_field, import_reporter
        )
        # For every case...
        for case_num, row_to_facility_map in case_map.items():
            with transaction.atomic():
                # Create the case...
                try:
                    case = Case.objects.create(batch=batch, case_num=case_num)
                # ...or report an error if we can't
                except django.db.utils.IntegrityError as error:
                    import_reporter.add_sheet_error(
                        {"error_type": "IntegrityError", "error": str(error)}
                    )
                # If the case is created, we now need to create all of its Facilities
                else:
                    # For every Facility dict...
                    for row_num, facility_dict in row_to_facility_map.items():
                        # ...create the Facility in the DB...
                        facility_error = create_facility(
                            header_field_map, facility_dict, case
                        )
                        # ...and report an error if it fails
                        if facility_error:
                            header, error = facility_error
                            import_reporter.add_row_error(header, row_num, error)

    if import_reporter.report:
        error_summary = import_reporter.generate_error_summary()
        batch.import_error_summary = json.dumps(error_summary, indent=2)
        tqdm.write(batch.import_error_summary)
        batch.save()

    return import_reporter


def process_excel_directory(dir_path, threshold=None, pattern=r".*\.(xls.?|csv)$"):
    """Import each file in the given dir_path matching the given pattern"""

    files = [
        os.path.join(dir_path, f) for f in os.listdir(dir_path) if re.search(pattern, f)
    ]
    max_fn_len = max([len(os.path.basename(filename)) for filename in files])
    report = {}
    sorted_files = tqdm(sorted(files), unit="files")
    for file_path in sorted_files:
        sorted_files.set_description(
            f"Processing {os.path.basename(file_path):{max_fn_len}}"
        )
        import_reporter = process_excel_file(file_path, threshold)
        if import_reporter:
            report[os.path.basename(file_path)] = import_reporter
    return report


@transaction.atomic
def main():
    sys.excepthook = excepthook
    args = parse_args()
    if args.interactive:
        global INTERACTIVE
        INTERACTIVE = True

    if os.path.isdir(args.path):
        reports = process_excel_directory(
            args.path, threshold=args.threshold, pattern=args.pattern
        )
    elif os.path.isfile(args.path):
        reports = process_excel_file(args.path, threshold=args.threshold)
    else:
        raise ValueError(f"Given path {args.path!r} is not a directory or file!")

    print("Reports:")
    # print(json.dumps(reports, indent=2, sort_keys=True))

    print("-" * 80)

    total_processed = len(reports)
    total_without_errors = 0
    all_unmapped_headers = set()
    all_duplicate_headers = set()
    for filename, report in reports.items():
        if not report.has_errors():
            total_without_errors += 1
        else:
            print(f"One or more errors while importing {filename!r}")

        all_unmapped_headers.update(report.report["header_errors"]["unmapped_headers"])
        all_duplicate_headers.update(
            report.report["header_errors"]["duplicate_headers"]
        )

        # pprint(report.report)

    print("Summary:")
    print(
        f"{total_without_errors}/{total_processed} "
        f"({total_without_errors / total_processed * 100:.2f}%) files imported without any errors"
    )

    print("All unmapped headers:")
    for header in sorted(all_unmapped_headers, key=str):
        print(repr(header))

    print("All duplicate headers:")
    for header in sorted(all_duplicate_headers, key=str):
        print(repr(header))

    if args.dry_run:
        raise ManualRollback("DRY RUN; ROLLING BACK CHANGES")


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "path",
        help=(
            "The path to an Excel application "
            "(or .csv representation), or a directory thereof"
        ),
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help=(
            "Roll back all database changes after execution. Note that "
            "this will leave gaps in the PKs where created objects were rolled back"
        ),
    )
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
        default=0.7,
        help="Threshold of invalid cells which constitute an invalid row.",
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

    return parser.parse_args()


if __name__ == "__main__":
    try:
        main()
    except ManualRollback as error:
        print(error)
