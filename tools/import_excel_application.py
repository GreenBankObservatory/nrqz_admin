#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""docstring"""

import django

django.setup()

import argparse
from collections import namedtuple
from glob import glob
import json
import os
from pprint import pprint, pformat
import sys
import traceback

import pyexcel

from django.db import transaction
from django.db import models


from submission.models import Attachment, Submission, Facility
from tools.field_import import facility_field_map


INTERACTIVE = False


# Each Excel file is represented by a Submission
# Each row in the "From Applicant" sheet is represented by a Facility




def load_rows(book):
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


MissingHeaderReport = namedtuple("MissingHeaderReport", ["header"])
ConversionErrorReport = namedtuple(
    "ConversionErrorReport", ["error", "value", "importer"]
)
ValidationErrorReport = namedtuple("ValidationErrorReport", ["error", "field"])


# def extract_submission_data(book):

# def create_submission_from_rows(rows):
#     """Create Submission object(s?) from given rows"""


def examine_tb(tb):
    frame = list(traceback.walk_tb(tb))[-1][0]
    # If this frame contains a "self" object that is an instance of a Django Field...
    if "self" in frame.f_locals and isinstance(frame.f_locals["self"], models.Field):
        # ...then we can examine it to determine which field it is
        return frame.f_locals["self"]


def excepthook(type_, value, tb):
    if type_ == ManualRollback:
        return
    import ipdb

    # Print the exception, as we would expect
    traceback.print_exception(type_, value, tb)
    # Then grab the last frame from it
    thing = examine_tb(tb)
    if thing:
        print(f"Error ocurred in relation to field: {thing}", file=sys.stderr)
    # Otherwise just drop into an interactive shell
    else:
        if INTERACTIVE:
            ipdb.post_mortem(tb)

def indentify_invalid_rows(rows, threshold=0.7):
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


@transaction.atomic
def process_excel_file(excel_path):
    """Create objects from given path"""

    print("Opening workbook")
    book = pyexcel.get_book(file_name=excel_path)
    print("...done")
    print("Loading rows...")
    rows = load_rows(book)
    print("...done")

    # Annotate each row with its original index (1-indexed). This
    # is so that we can reference them by this later
    rows = [row + [row_num] for row_num, row in enumerate(rows, 1)]

    # Get the indexes of all invalid rows...
    invalid_row_indices = indentify_invalid_rows(rows)
    for index in sorted(invalid_row_indices, reverse=True):
        print(f"Deleted invalid row {index}")
        # ...then delete them
        del rows[index]

    headers = rows[0]
    data = rows[1:]

    submission = Submission.objects.create()

    excel_attachment = Attachment.objects.create(
        path=excel_path, comments="Attached by import_excel_application.py"
    )
    submission.attachments.add(excel_attachment)
    missing_header_handlers = set()
    conversion_errors = []
    validation_errors = []

    errors_by_header = {}

    discovered_headers = {}

    for row in data:
        # Pull out the row number from the row...
        row_num = row[-1]
        # ...then delete it
        del row[-1]
        facility_dict = {}
        for ci, cell in enumerate(row):
            importer = None
            header = headers[ci]
            try:
                importer = facility_field_map[header]
            except KeyError:
                missing_header_handlers.add(header)
                errors_by_header[header] = {
                    "converter": None,
                    "field": None,
                    "error_type": "header",
                    "error": "No header mapped!"
                }
                discovered_headers[header] = None
            else:
                discovered_headers[header] = importer.field
                try:
                    facility_dict[importer.field] = importer.converter(cell)
                except Exception as error:
                    conversion_errors.append(
                        f"Could not convert value {cell!r} using converter "
                        f"{importer.converter.__name__}: {error}"
                    )
                    es = {
                        "error": str(error),
                        "value": cell
                    }
                    if header in errors_by_header:
                        errors_by_header[header]["row_errors"][row_num] = es
                    else:
                        errors_by_header[header] = {
                            "converter": importer.converter.__name__,
                            "field": importer.field,
                            "error_type": "conversion",
                            "row_errors": {row_num: es}
                        }
                        

        facility = Facility(**facility_dict, submission=submission)
        try:
            with transaction.atomic():
                facility.save()
        except (django.core.exceptions.ValidationError, ValueError, TypeError) as error:
            field = examine_tb(error.__traceback__)
            inverted = {value: key for key, value in discovered_headers.items() if value is not None}
            header = inverted[field.name]
            validation_errors.append(f"Field '{field}' encountered error: {error}")
            errors_by_header[header] = {
                "field": field.name,
                "error_type": "validation",
                "error": str(error.args),
            }
        else:
            print(f"Created {facility}")

    print(f"Created {len(data)} Facility objects")
    print("-" * 80)

    ret = {}
    if missing_header_handlers:
        ret["missing_header_handlers"] = list(missing_header_handlers)
    if conversion_errors:
        ret["conversion_errors"] = conversion_errors
    if validation_errors:
        ret["validation_errors"] = validation_errors

    submission.import_report = json.dumps(errors_by_header, indent=2, sort_keys=True)
    submission.save()
    return ret


def process_excel_directory(dir_path):
    report = {}
    for excel_path in sorted(glob(os.path.join(dir_path, "*.xls*"))):
        print(f"Processing {excel_path}")
        file_report = process_excel_file(excel_path)
        if file_report:
            report[os.path.basename(excel_path)] = file_report
    return report

def process_csv_directory(dir_path):
    report = {}
    for csv_path in sorted(glob(os.path.join(dir_path, "*.csv"))):
        print(f"Processing {csv_path}")
        file_report = process_excel_file(csv_path)
        if file_report:
            report[os.path.basename(csv_path)] = file_report
    return report


class ManualRollback(Exception):
    pass


@transaction.atomic
def main():
    sys.excepthook = excepthook
    args = parse_args()
    if args.interactive:
        global INTERACTIVE
        INTERACTIVE = True

    if os.path.isdir(args.path):
        reports = process_csv_directory(args.path)
    elif os.path.isfile(args.path):
        reports = process_excel_file(args.path)
    else:
        raise ValueError("womp womp")

    print("Reports:")
    print(json.dumps(reports, indent=2, sort_keys=True))

    if args.dry_run:
        raise ManualRollback("DRY RUN; ROLLING BACK CHANGES")


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("path")
    parser.add_argument("-d", "--dry-run", action="store_true")
    parser.add_argument("-i", "--interactive", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    try:
        main()
    except ManualRollback as error:
        print(error)
