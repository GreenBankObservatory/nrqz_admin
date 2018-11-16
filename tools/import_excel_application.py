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
from pprint import pprint, pformat
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
from cases.forms import FacilityForm
from tools.excelfieldmap import facility_field_map
from tools.import_report import ImportReport


DEFAULT_THRESHOLD = 0.7


class ManualRollback(Exception):
    pass


def load_excel_data(path, import_reporter):
    """Given path to Excel file, extract data and return"""

    book = pyexcel.get_book(file_name=path)

    primary_sheet = "Working Data"

    try:
        sheet = book.sheet_by_name(primary_sheet)
    except KeyError:
        sheet = book.sheet_by_index(0)
        import_reporter.add_sheet_name_error(
            f"Sheet {primary_sheet!r} not found; used first sheet instead: {sheet.name!r}"
        )

    # try:
    #     from_applicant = book.sheet_by_name("From Applicant")
    # except KeyError:
    #     import ipdb

    #     ipdb.set_trace()

    # sheet = working_data
    return sheet.array


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
                    "conversion_error",
                    {
                        "row": row_num,
                        "header": header,
                        "converter": importer.converter.__name__,
                        "field": importer.to_field,
                        "error": str(error),
                        "value": cell,
                    },
                )
        else:
            # tqdm.write(
            #     "Either no field importer or no importer.to_field; skipping "
            #     f"value {cell!r} for header {header!r}!"
            # )
            continue

    return facility_dict


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
        try:
            row_num = int(row_num)
        except ValueError:
            import_reporter.add_row_error(
                "invalid_row_num",
                {
                    "row": row_num,
                    "error": f"Could not convert {row_num} to a number! Check original Excel file for issues",
                },
            )
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
                "nrqz_id_error",
                {
                    "row": row_num,
                    "header": header,
                    "error": str(error),
                    "value": facility_dict[nrqz_id_field],
                },
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


def get_unmapped_fields():
    excluded_fields = ["location", "asr_is_from_applicant", "case", "structure"]
    facility_fields = [
        field for field in FacilityForm.Meta.fields if field not in excluded_fields
    ]

    mapped_fields = [
        importer.to_field
        for importer in facility_field_map.values()
        if importer is not None
    ]
    unmapped_fields = [field for field in facility_fields if field not in mapped_fields]
    return unmapped_fields


class BatchImportException(Exception):
    pass


class BatchImportError(BatchImportException):
    pass


class BatchRejectionError(BatchImportError):
    pass


class DuplicateCaseError(BatchRejectionError):
    pass


class UnmappedFieldError(BatchRejectionError):
    pass


class MissingNrqzIdError(BatchRejectionError):
    pass


class FacilityValidationError(BatchRejectionError):
    pass


class TooManyUnmappedHeadersError(BatchRejectionError):
    pass


# TODO: Probably not needed here...
@transaction.atomic
def create_facility(facility_dict, case, import_reporter, durable=False):
    import_reporter.facilities_processed += 1
    # TODO: Alter FacilityForm so that it uses case num instead of ID somehow
    facility_dict = {**facility_dict, "case": case.id if case else None}
    facility_form = FacilityForm(facility_dict)
    if facility_form.is_valid():
        facility = facility_form.save()
        import_reporter.audit_facility_success(facility)
        import_reporter.facilities_created.append(facility)
        return None
    else:
        if durable:
            import_reporter.audit_facility_error(
                case, facility_dict, facility_form.errors.as_data()
            )
        else:
            raise FacilityValidationError(
                f"Facility {facility_dict} failed validation:\n{pformat(facility_form.errors.as_data())}"
            )

        import_reporter.facilities_not_created.append(facility_dict)
        useful_errors = {
            field: {"value": facility_dict[field], "errors": errors}
            for field, errors in facility_form.errors.as_data().items()
        }
        return useful_errors


@transaction.atomic
def create_case(batch, case_num, row_to_facility_map, import_reporter, durable=False):
    import_reporter.cases_processed += 1
    # Create the case...
    try:
        case = Case.objects.create(batch=batch, case_num=case_num)
    # ...or report an error if we can't
    except django.db.utils.IntegrityError as error:
        dce = DuplicateCaseError(
            f"Batch '{batch}' rejected due to duplicate case: {case_num}"
        )
        import_reporter.add_case_error("IntegrityError", error)
        import_reporter.cases_not_created.append(case_num)
        if not durable:
            raise dce from error
        case = None
    # If the case is created, we now need to create all of its Facilities
    else:
        import_reporter.cases_created.append(case)
    # For every Facility dict...
    for row_num, facility_dict in row_to_facility_map.items():
        facility_errors = create_facility(facility_dict, case, import_reporter, durable)
        if facility_errors:
            import_reporter.add_row_error(
                "validation_error", {"row": row_num, "error": facility_errors}
            )


@transaction.atomic
def create_batch(excel_path):
    # A Batch representing this Excel file
    batch = Batch.objects.create(
        name=os.path.basename(excel_path), comments=f"Created by {__file__}"
    )

    # An attachment referencing the original Excel (or .csv) file
    batch.attachments.add(
        Attachment.objects.create(path=excel_path, comments=f"Attached by {__file__}")
    )

    return batch


def process_case_map(batch, case_map, import_reporter, durable):
    for case_num, row_to_facility_map in case_map.items():
        create_case(batch, case_num, row_to_facility_map, import_reporter, durable)


@transaction.atomic
def process_excel_file(
    excel_path, import_reporter, durable=False, threshold=DEFAULT_THRESHOLD
):
    """Create objects from given path"""

    batch = create_batch(excel_path)
    import_reporter.batch = batch

    rows = load_excel_data(excel_path, import_reporter)
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

    unmapped_header_ratio = len(unmapped_headers) / len(headers)
    if unmapped_header_ratio > threshold:
        import_reporter.add_too_many_unmapped_headers_error(
            f"{unmapped_header_ratio * 100:.2f}% of headers are not mapped; batch rejected"
        )
        if not durable:
            raise TooManyUnmappedHeadersError(
                f"{unmapped_header_ratio * 100:.2f}% of headers are not mapped; batch rejected"
            )

    unmapped_fields = get_unmapped_fields()
    if unmapped_fields:
        import_reporter.set_unmapped_fields(unmapped_fields)
        if not durable:
            raise UnmappedFieldError(
                f"Batch '{batch}' rejected due to unmapped DB fields: {unmapped_fields}"
            )

    # Determine the field in which our NRQZ ID string has been stored
    # This will be used later to parse out the case number
    nrqz_id_field = derive_nrqz_id_field(header_field_map)
    if nrqz_id_field:
        # Create our case->row_num->facility map
        case_map = create_case_map(
            header_field_map, data, nrqz_id_field, import_reporter
        )
        # Create all Cases and Facilities in the case_map
        process_case_map(batch, case_map, import_reporter, durable)
    else:
        import_reporter.add_case_error(
            "MissingNrqzIdError", MissingNrqzIdError("Could not derive NRQZ ID!")
        )
        if not durable:
            raise MissingNrqzIdError("Could not derive NRQZ ID!")

    if import_reporter.report:
        error_summary = import_reporter.get_non_fatal_errors()
        batch.import_error_summary = json.dumps(error_summary, indent=2)
        tqdm.write(excel_path)
        tqdm.write(batch.import_error_summary)
        batch.save()

    if import_reporter.has_fatal_errors():
        raise BatchRejectionError("One or more fatal errors has occurred!")

    return import_reporter


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


# @transaction.atomic()
def process_excel_files(files, durable=False, threshold=DEFAULT_THRESHOLD):
    """Import each file in the given dir_path matching the given pattern"""
    longest_filename = max([len(os.path.basename(filename)) for filename in files])
    report = {}
    files_tqdm = tqdm(sorted(files), unit="files")
    for file_path in files_tqdm:
        files_tqdm.set_description(
            f"Processing {os.path.basename(file_path):{longest_filename}}"
        )

        import_reporter = ImportReport(file_path)
        try:
            # with transaction.atomic():
            process_excel_file(file_path, import_reporter, durable, threshold)
        except BatchRejectionError as error:
            # This is a sanity check to ensure that the Batch has in fact been
            # rolled back. Since we are tracking the Batch object inside our
            # import_reporter, we can attempt to refresh it from the DB. We
            # expect that this will fail, but if for some reason it succeeds
            # then we treat this as a fatal error
            try:
                import_reporter.batch.refresh_from_db()
            except Batch.DoesNotExist:
                tqdm.write(f"Successfully rejected Batch {file_path}: {error}")
            else:
                raise ValueError("Batch should have been rolled back, but wasn't!")
        else:
            # Similarly, we want to ensure that the Batch has been committed
            # if there are no fatal errors in importing it
            try:
                import_reporter.batch.refresh_from_db()
            except Batch.DoesNotExist as error:
                raise ValueError(
                    "Batch should have been committed, but wasn't!"
                ) from error

        report[os.path.basename(file_path)] = import_reporter
    return report


def process_reports(processed_files, reports):

    total_files_processed = len(processed_files)
    print(f"Processed {total_files_processed} files")
    total_cases_created = 0
    total_cases_processed = 0
    total_facilities_created = 0
    total_facilities_processed = 0
    total_files_without_any_errors = 0
    total_files_without_fatal_errors = 0

    report_summary = {}
    # all_unmapped_headers = set()
    # all_unmapped_fields = set()
    # all_duplicate_headers = set()
    for filename, import_reporter in reports.items():
        for error_category, errors_by_type in import_reporter.report.items():
            if error_category not in ["batch_errors", "sheet_errors"]:
                continue
            if error_category not in report_summary:
                report_summary[error_category] = {}
            for error_type, errors_ in errors_by_type.items():

                if error_type in report_summary[error_category]:
                    report_summary[error_category][error_type].update(errors_)
                else:
                    report_summary[error_category][error_type] = set(errors_)

        total_cases_processed += import_reporter.cases_processed
        total_cases_created += len(import_reporter.cases_created)
        total_facilities_created += len(import_reporter.facilities_created)
        total_facilities_processed += import_reporter.facilities_processed
        if not import_reporter.has_errors():
            total_files_without_any_errors += 1
        if not import_reporter.has_fatal_errors():
            total_files_without_fatal_errors += 1

        # else:
        #     print(f"One or more errors while importing {filename!r}")

    successful_import_reporters = [
        report for report in reports.values() if not report.has_fatal_errors()
    ]
    total_batches_created = len(successful_import_reporters)
    print("Totals:")
    print(
        f"  Successfully created {total_batches_created}/{len(reports)} Batches, "
        f"{total_cases_created}/{total_cases_processed} Cases, "
        f"and {total_facilities_created}/{total_facilities_processed} Facilities:"
    )
    # for filename, import_reporter in reports.items():
    #     print(f"  Batch {filename}:")
    #     print("     Cases created:")
    #     for case in import_reporter.cases_created:
    #         print(f"      Case {case}: {case.facilities.count()} Facilities")

    #     print("     Cases not created:")
    #     for case in import_reporter.cases_not_created:
    #         print(f"      Case {case}: {case.facilities.count()} Facilities")

    print(f"  Total cases processed: {total_cases_processed}")
    print(f"  Total facilities created: {total_facilities_created}")
    print(f"  Total facilities processed: {total_facilities_processed}")
    print(
        f"{total_files_without_any_errors}/{total_files_processed} "
        f"({total_files_without_any_errors / total_files_processed * 100:.2f}%) files imported without any errors"
    )

    print("-" * 80)
    print("Summary:")
    for error_category, errors_by_type in report_summary.items():
        print(f"  Summary of ALL {error_category!r}:")
        for error_type, errors_ in errors_by_type.items():
            print(f"    Unique {error_type!r}:")
            for error_ in sorted(errors_):
                formatted_error = "\n".join(
                    [f"      {line}" for line in pformat(error_).split("\n")]
                )
                print(formatted_error)

    print("-" * 80)
    print("Report:")
    for filename, import_reporter in reports.items():
        fatal_errors = import_reporter.get_fatal_errors()
        if import_reporter.has_errors(fatal_errors):
            print(f"  Batch {filename} rejected:")
            for error_category, errors_by_type in fatal_errors.items():
                print(f"    {error_category!r} errors by type:")
                for error_type, errors_ in errors_by_type.items():
                    print(f"      {error_type!r}:")
                    for error_ in errors_:
                        formatted_error = "\n".join(
                            [f"        {line}" for line in pformat(error_).split("\n")]
                        )
                        print(formatted_error)
        else:
            non_fatal_errors = import_reporter.get_non_fatal_errors()
            if import_reporter.has_errors(non_fatal_errors):
                print(f"  Batch {filename} created with the following caveats:")
                formatted_summary = "\n".join(
                    [
                        f"        {line}"
                        for line in pformat(non_fatal_errors).split("\n")
                    ]
                )
                print(formatted_summary)
            else:
                print(f"  Batch {filename} created without any issues")


@transaction.atomic
def main():
    # sys.excepthook = excepthook
    args = parse_args()
    files_to_process = determine_files_to_process(args.paths, pattern=args.pattern)
    reports = process_excel_files(
        files_to_process, durable=args.durable, threshold=args.threshold
    )

    print("-" * 80)
    process_reports(files_to_process, reports)

    if args.dry_run:
        raise ManualRollback("DRY RUN; ROLLING BACK CHANGES")


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help=(
            "The paths to Excel applications to process "
            "(or .csv representation), or a directories thereof"
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
        "-p",
        "--pattern",
        default=r".*\.(xls.?|csv)$",
        help=(
            "Regular expression used to identify Excel application files. "
            "Used only when a directory is given in path"
        ),
    )
    parser.add_argument(
        "-D",
        "--durable",
        default=False,
        action="store_true",
        help=(
            "If set, processing on a given batch will continue past all possible errors"
        ),
    )
    parser.add_argument(
        "-t",
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="Threshold of invalid headers which constitute an invalid sheet.",
    )

    parsed_args = parser.parse_args()
    if not 0 <= parsed_args.threshold <= 1:
        parser.error("--threshold must be between 0 and 1")
    return parsed_args


if __name__ == "__main__":
    try:
        main()
    except ManualRollback as error:
        print(error)
