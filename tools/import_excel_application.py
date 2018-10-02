#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""docstring"""

import django

django.setup()

import argparse
from pprint import pprint

import pyexcel

from submission.models import Attachment, Submission, Facility

# Each Excel file is represented by a Submission
# Each row in the "From Applicant" sheet is represented by a Facility

# def dms_to_dd(d, m, s):
#     dd = d + float(m)/60 + float(s)/3600
#     return dd


def load_rows(book):
    sheet = book.to_dict()["From Applicant"]
    # columns = sheet[0]
    # for record in sheet[1:3]:
    # print(record)
    # import ipdb; ipdb.set_trace()
    return sheet[1:]


# def extract_submission_data(book):

# def create_submission_from_rows(rows):
#     """Create Submission object(s?) from given rows"""


def coerce_bool(value):
    clean_value = value.strip().lower()
    if clean_value == "yes":
        return True
    elif clean_value == "no":
        return False
    else:
        raise ValueError("Could not determine truthiness of value {!r}".format(value))


def process_rows(rows, excel_path):
    """Create objects from given rows"""


    submission = Submission.objects.create()

    excel_attachment = Attachment.objects.create(
        path=excel_path, comments="Attached by import_excel_application.py"
    )
    submission.attachments.add(excel_attachment)

    for row in rows:
        facility = Facility(
            freq_low=row[0],
            site_name=row[1],
            call_sign=row[2],
            fcc_file_number=row[3],
            latitude=row[4],
            longitude=row[5],
            amsl=row[6],
            agl=row[7],
            freq_high=row[8],
            bandwidth=row[9],
            max_output=row[10],
            antenna_gain=row[11],
            system_loss=row[12],
            main_beam_orientation=row[13],
            mechanical_downtilt=row[14],
            electrical_downtilt=row[15],
            antenna_model_number=row[16],
            nrqz_id=row[17],
            tx_per_sector=row[18],
            tx_antennas_per_sector=row[19],
            technology=row[20],
            uses_split_sectorization=coerce_bool(row[21]),
            uses_cross_polarization=coerce_bool(row[22]),
            tx_power_pos_45=row[23],
            tx_power_neg_45=row[24],
            comments=row[25],
            submission=submission,
        )
        print(facility)
        facility.save()


def main():
    args = parse_args()
    book = pyexcel.get_book(file_name=args.path)
    rows = load_rows(book)
    process_rows(rows, args.path)


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("path")
    return parser.parse_args()


if __name__ == "__main__":
    main()
