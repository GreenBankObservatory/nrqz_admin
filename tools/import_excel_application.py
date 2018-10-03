#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""docstring"""

import django

django.setup()

import argparse
from collections import namedtuple
from glob import glob
import os
from pprint import pprint, pformat
import sys
import traceback

import pyexcel

from django.db import transaction
from django.db import models


from submission.models import Attachment, Submission, Facility

INTERACTIVE = False


# Each Excel file is represented by a Submission
# Each row in the "From Applicant" sheet is represented by a Facility

# def dms_to_dd(d, m, s):
#     dd = d + float(m)/60 + float(s)/3600
#     return dd


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


def coerce_bool(value):
    clean_value = value.strip().lower()
    if clean_value.startswith("yes"):
        return True
    elif clean_value.startswith("no"):
        return False
    elif clean_value in ["", "na"]:
        return None
    else:
        raise ValueError("Could not determine truthiness of value {!r}".format(value))


def coerce_num(value):
    if value in ["", "na", "n/a", "no"]:
        return None
    return value


class FieldImport:
    def __init__(self, field, converter, known_headers):
        # Headers the field could potentially be associated with
        self.field = field
        # Function to convert/clean data
        self.converter = converter if converter else self.default_converter
        self.known_headers = known_headers

    def default_converter(self, value):
        return value

    def __repr__(self):
        return f"{self.field} <{self.converter.__name__}>: {self.known_headers}"

    # def process(self, ):


field_importers = [
    FieldImport(
        field="freq_low", converter=coerce_num, known_headers=["Freq Low (MHz)"]
    ),
    FieldImport(field="site_name", converter=None, known_headers=["Site Name"]),
    FieldImport(field="call_sign", converter=None, known_headers=["Call Sign"]),
    FieldImport(
        field="fcc_file_number", converter=None, known_headers=["FCC File Number"]
    ),
    FieldImport(field="latitude", converter=None, known_headers=["LAT (dd mm ss.ss)"]),
    FieldImport(
        field="longitude",
        converter=None,
        known_headers=["LON (-dd mm ss.ss)", "LON (dd mm ss.ss)"],
    ),
    FieldImport(field="amsl", converter=coerce_num, known_headers=["AMSL (m)"]),
    FieldImport(field="agl", converter=coerce_num, known_headers=["AGL (m)"]),
    FieldImport(
        field="freq_high", converter=coerce_num, known_headers=["Freq High (MHz)"]
    ),
    FieldImport(
        field="bandwidth",
        converter=coerce_num,
        known_headers=["Bandwidth (MHz)", "Minimum Bandwidth (MHz) utilized per TX"],
    ),
    FieldImport(
        field="max_output",
        converter=coerce_num,
        known_headers=["Max Tx Pwr (W)", "Max Output Pwr (W) Per TX"],
    ),
    FieldImport(
        field="antenna_gain", converter=coerce_num, known_headers=["Antenna Gain (dBi)"]
    ),
    FieldImport(
        field="system_loss", converter=coerce_num, known_headers=["System Loss (dB)"]
    ),
    FieldImport(
        field="main_beam_orientation",
        converter=None,
        known_headers=["Main Beam Orientation (All Sectors)"],
    ),
    FieldImport(
        field="mechanical_downtilt",
        converter=None,
        known_headers=["Mechanical Downtilt (All Sectors)"],
    ),
    FieldImport(
        field="electrical_downtilt",
        converter=None,
        known_headers=["Electrical Downtilt (All Sectors)"],
    ),
    FieldImport(
        field="antenna_model_number", converter=None, known_headers=["Antenna Model #"]
    ),
    FieldImport(
        field="nrqz_id",
        converter=None,
        known_headers=["NRQZ ID (to be assigned by NRAO)", "NRQZ ID"],
    ),
    FieldImport(
        field="tx_per_sector",
        converter=coerce_num,
        known_headers=[
            "Number of Transmitters per sector",
            "Total number of TXers (or No. of RRH's ports with feed power) per sector",
            "Number of TXers per sector",
        ],
    ),
    FieldImport(
        field="tx_antennas_per_sector",
        converter=coerce_num,
        known_headers=[
            "Number of TX antennas per sector",
            "Number of TX antennas per sector (Each polarization fed with TX power is considered an antenna).",
        ],
    ),
    FieldImport(
        field="technology",
        converter=None,
        known_headers=[
            "Technology 2G, 3G, 4G, other (specify)",
            "Technology i.e. FM, 2G, 3G, 4G, GSM, LTE, UMTS, CDMA2000 (specify other)",
        ],
    ),
    FieldImport(
        field="uses_split_sectorization",
        converter=coerce_bool,
        known_headers=[
            "This faciltiy uses Split sectorization (Yes or No)",
            "This faciltiy uses Split sectorization (or dual-beam sectorization) Indidate Yes or No",
        ],
    ),
    FieldImport(
        field="uses_cross_polarization",
        converter=coerce_bool,
        known_headers=[
            "This facility uses Cross polarization (Yes or No)",
            "This facility uses Cross polarization   Indicate Yes or No",
        ],
    ),
    FieldImport(
        field="quad_or_octal_polarization",
        converter=coerce_bool,
        known_headers=[
            "If this facility uses Quad or Octal polarization, specify type here"
        ],
    ),
    FieldImport(
        field="num_quad_or_octal_ports_with_feed_power",
        converter=coerce_num,
        known_headers=["Number of Quad or Octal ports with  feed power"],
    ),
    FieldImport(
        field="tx_power_pos_45",
        converter=coerce_num,
        known_headers=[
            'If YES to Col. "W", then what is the Max TX output PWR at +45 degrees'
        ],
    ),
    FieldImport(
        field="tx_power_neg_45",
        converter=coerce_num,
        known_headers=[
            'If YES to Col. "W", then what is the Max TX output PWR at -45 degrees'
        ],
    ),
    FieldImport(
        field="comments",
        converter=None,
        known_headers=["", "Additional information or comments from the applicant"],
    ),
    FieldImport(
        field="num_pols_with_feed_power", converter=coerce_num, known_headers=[]
    ),
]

# Generate a map of known_header->importer by "expanding" the known_headers of each FieldImporter
# In this way we can easily and efficiently look up a given header and find its associated importer
facility_field_map = {}
for importer in field_importers:
    for header in importer.known_headers:
        facility_field_map[header] = importer


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

    invalid_rows = indentify_invalid_rows(rows)
    for index in sorted(invalid_rows, reverse=True):
        print(f"Deleted invalid row {index}")
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

    for row in data:
        facility_dict = {}
        for ci, cell in enumerate(row):
            fi = None
            try:
                fi = facility_field_map[headers[ci]]
            except KeyError:
                missing_header_handlers.add(headers[ci])
            else:
                try:
                    facility_dict[fi.field] = fi.converter(cell)
                except Exception as error:
                    conversion_errors.append(
                        f"Could not convert value {cell!r} using converter "
                        f"{fi.converter.__name__}: {error}"
                    )

        facility = Facility(**facility_dict, submission=submission)
        try:
            with transaction.atomic():
                facility.save()
        except ValueError as error:
            field = examine_tb(error.__traceback__)
            validation_errors.append(f"Field '{field}' encountered error: {error}")

    print(f"Created {len(data)} Facility objects")
    print("-" * 80)

    ret = {}
    if missing_header_handlers:
        ret["missing_header_handlers"] = list(missing_header_handlers)
    if conversion_errors:
        ret["conversion_errors"] = conversion_errors
    if validation_errors:
        ret["validation_errors"] = validation_errors
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
    import json

    print(json.dumps(reports, indent=2, sort_keys=True))
    # for file_name, file_report in reports.items():
    #     print(f"Reporting on: {file_name}")
    #     for report in file_report:
    #         print(report)
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
