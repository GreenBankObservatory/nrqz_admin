#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Import Excel NRQZ application forms into the DB

Each Excel file creates a Batch. Each case number represents a Submission.
Each data row in the Excel file creates a Facility.

Any files matching *.xls* or *.csv will be considered applications and
an attempt will be made to import them
"""

import argparse
from collections import namedtuple, OrderedDict
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

from submission.models import Attachment, Batch, Submission, Facility
from tools.excelfieldmap import facility_field_map
from tools.error_reporter import ErrorReporter


INTERACTIVE = False


class ManualRollback(Exception):
    pass


def load_rows(path):
    book = pyexcel.get_book(file_name=path)
    book_dict = book.to_dict()

    try:
        sheet = book_dict["From Applicant"]
    except KeyError:
        print(
            "WARNING: Could not find sheet 'From Applicant'. Falling back to first sheet"
        )
        # TODO: More robust
        if len(book) != 1:
            print("ERROR: More than one sheet!")

        sheet = book.sheet_by_index(0).array

    return sheet


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
        print(f"Error ocurred in relation to field: {field}", file=sys.stderr)
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
                # print(f"Found invalid cell: {cell!r}")
                invalid_cells += 1

        if invalid_cells / len(row) > threshold:
            print(f"Found invalid row {ri} (>{threshold * 100}% cells invalid): {row}")
            invalid_row_indices.append(ri)

    return invalid_row_indices


def determine_actual_headers(headers):
    return OrderedDict(
        [(header, facility_field_map.get(header, None)) for header in headers]
    )


def create_facility_dict_from_row(header_field_map, row, error_reporter, row_num):

    facility_dict = {}
    for header, importer, cell in zip(
        header_field_map.keys(), header_field_map.values(), row
    ):
        if importer:
            try:
                facility_dict[importer.to_field] = importer.converter(cell)
            except (ValueError) as error:
                error_reporter.add_row_error(
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
            print(f"No converter; skipping value {cell!r} for header {header!r}!")
            continue

    return facility_dict


def create_facility(header_field_map, facility_dict, submission):
    facility = Facility(**facility_dict, submission=submission)
    try:
        with transaction.atomic():
            facility.save()
    except (django.core.exceptions.ValidationError, ValueError, TypeError) as error:
        field = derive_field_from_validation_error(error.__traceback__)
        field_header_map = {
            value.field: key
            for key, value in header_field_map.items()
            if value is not None
        }
        value = facility_dict[field]
        derived_header = field_header_map[field.name]
        error = (derived_header, {
            "converter": facility_field_map[derived_header].converter.__name__,
            "field": field.name,
            "error_type": "validation",
            "error": str(error.args),
            "value": str(value),
        })
        facility = None
    else:
        error = None
        # print(f"Created {facility}")

    return facility, error

# https://regex101.com/r/gRPTN8/1
nrqz_id_regex_str = r"^(?P<case_num>\d+)[\s_\*]+(?:\(.*\)[\s_]+)?(?P<site_name>(?:(?:\w+\s+)?\S{5}|\D+))[\s_]+(?P<facility_name>\S+)$"
nrqz_id_regex = re.compile(nrqz_id_regex_str)
nrqz_id_regex_fallback_str = r"^(?P<case_num>\d+).*"
nrqz_id_regex_fallback = re.compile(nrqz_id_regex_fallback_str)


def derive_case_num_from_nrqz_id(nrqz_id):
    try:
        match = nrqz_id_regex.match(nrqz_id)
    except TypeError:
        print(f"nrqz_id: {nrqz_id!r}")

    if not match:
        match = nrqz_id_regex_fallback.match(nrqz_id)
        if not match:
            raise ValueError(
                f"Could not parse NRQZ ID '{nrqz_id}' using "
                f"'{nrqz_id_regex_str}' or '{nrqz_id_regex_fallback_str}'!"
            )
    return match["case_num"]


def create_submission_map(header_field_map, data, nrqz_id_field, error_reporter):
    submission_map = {}
    for row in data:
        # Pull out the row number from the row...
        row_num = row[-1]
        # ...then delete it
        del row[-1]
        facility_dict = create_facility_dict_from_row(header_field_map, row, error_reporter, row_num)
        try:
            case_num = derive_case_num_from_nrqz_id(str(facility_dict[nrqz_id_field]))
        except ValueError as error:
            field_header_map = {
                value.to_field: key
                for key, value in header_field_map.items()
                if value is not None
            }
            header = field_header_map[nrqz_id_field]
            error_reporter.add_row_error(header, row_num, {"error": str(error), "converter": None, "value": None})
        else:
            if case_num in submission_map:
                submission_map[case_num][row_num] = facility_dict
            else:
                submission_map[case_num] = {row_num: facility_dict}

    return submission_map


def derive_nrqz_id_field(fields):
    nrqz_id_fields = ["nrqz_id", "site_name"]
    for nrqz_id_field in nrqz_id_fields:
        if nrqz_id_field in fields:
            return nrqz_id_field

    return None



@transaction.atomic
def process_excel_file(excel_path, threshold=None):
    """Create objects from given path"""

    error_reporter = ErrorReporter(excel_path)


    # A Batch representing this Excel file
    batch = Batch.objects.create(
        name=os.path.basename(excel_path), comments=f"Created by {__file__}"
    )

    # An attachment referencing the original Excel (or .csv) file
    batch.attachments.add(
        Attachment.objects.create(path=excel_path, comments=f"Attached by {__file__}")
    )

    print("Opening workbook")
    rows = load_rows(excel_path)
    print("...done")
    # Annotate each row with its original index (1-indexed). This
    # is so that we can reference them by this later
    rows = [row + [row_num] for row_num, row in enumerate(rows, 1)]

    # Get the indexes of all invalid rows...
    invalid_row_indices = indentify_invalid_rows(rows, threshold)
    for index in sorted(invalid_row_indices, reverse=True):
        print(f"Deleted invalid row {index}")
        # ...then delete them
        del rows[index]

    # A list of the headers actually in the file
    headers = rows[0][:-1]
    # A list of rows containing data
    data = rows[1:]
    header_field_map = determine_actual_headers(headers)

    for header, field in header_field_map.items():
        if field is None:
            error_reporter.add_unmapped_header(header)

    nrqz_id_field = derive_nrqz_id_field(fields=[fm.to_field for fm in header_field_map.values() if fm])
    if not nrqz_id_field:
        error_reporter.add_sheet_error({
            "error_type": "case_num_not_found",
            "error": "No case number header found; tried site_name and nrqz_id",
        })
    else:
        submission_map = create_submission_map(header_field_map, data, nrqz_id_field, error_reporter)
        for case_num, row_to_facility_map in submission_map.items():
            submission = Submission.objects.create(batch=batch, case_num=case_num)
            for row_num, facility_dict in row_to_facility_map.items():
                facility, facility_error = create_facility(
                    header_field_map, facility_dict, submission
                )
                if facility_error:
                    header, error = facility_error
                    error_reporter.add_row_error(header, row_num, error)


    error_reporter.print_report()
    print("-" * 80)

    ret = {}
    if error_reporter.report:
        error_summary = error_reporter.generate_error_summary()
        batch.import_error_summary = json.dumps(error_summary, indent=2)
        ret["error_summary"] = error_summary
        batch.save()

    return ret


def process_excel_directory(dir_path, threshold=None, pattern=r".*\.(xls.?|csv)$"):
    """Import each file in the given dir_path matching the given pattern"""

    files = [
        os.path.join(dir_path, f) for f in os.listdir(dir_path) if re.search(pattern, f)
    ]
    report = {}
    for file_path in sorted(files):
        print(f"Processing {file_path}")
        file_report = process_excel_file(file_path, threshold)
        if file_report:
            report[os.path.basename(file_path)] = file_report
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
    print(json.dumps(reports, indent=2, sort_keys=True))

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
