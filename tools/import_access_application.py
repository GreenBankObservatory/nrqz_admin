#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""docstring"""


import argparse
import csv
from pprint import pprint

import django

django.setup()
from django.db import transaction

from submission.models import Attachment, Submission, Person
from tools.accessfieldmap import (
    applicant_field_mappers,
    contact_field_mappers,
    submission_field_mappers,
    get_combined_field_map,
)
from tools.import_excel_application import derive_field_from_validation_error

field_map = get_combined_field_map()


class ManualRollback(Exception):
    pass


def load_rows(path):
    with open(path, newline="", encoding="latin1") as file:
        return list(csv.reader(file))

_letters = [f"letter{i}" for i in range(1, 9)]

@transaction.atomic
def handle_row(field_importers, row):
    applicant_dict = {}
    contact_dict = {}
    submission_dict = {}

    for fi, value in zip(field_importers, row):
        if fi:
            if fi in applicant_field_mappers:
                applicant_dict[fi.to_field] = fi.converter(value)
            elif fi in contact_field_mappers:
                contact_dict[fi.to_field] = fi.converter(value)
            elif fi in submission_field_mappers:
                submission_dict[fi.to_field] = fi.converter(value)
            else:
                raise ValueError("Shouldn't be possible")

    found_report = dict(applicant=False, contact=False, submission=False)
    applicant = None
    if any(applicant_dict.values()):
        try:
            applicant = Person.objects.get(name=applicant_dict["name"])
            print(f"Found applicant {applicant}")
            found_report["applicant"] = True
        except Person.DoesNotExist:
            applicant = Person.objects.create(**applicant_dict)
            # print(f"Created applicant {applicant}")
        except Person.MultipleObjectsReturned:
            raise ValueError(applicant_dict)
    else:
        print("No applicant data; skipping")

    contact = None
    if any(contact_dict.values()):
        try:
            contact = Person.objects.get(name=contact_dict["name"])
            print(f"Found contact {contact}")
            found_report["contact"] = True
        except Person.DoesNotExist:
            contact = Person.objects.create(**contact_dict)
            # print(f"Created contact {contact}")
        except Person.MultipleObjectsReturned:
            raise ValueError(contact_dict)
    else:
        print("No contact data; skipping")

    if any(submission_dict.values()):
        try:
            submission = Submission.objects.get(case_num=submission_dict["case_num"])
            print(f"Found submission {submission}")
            found_report["submission"] = True
        except Submission.DoesNotExist:

            stripped_submission_dict = {}
            attachments = []
            for key, value in submission_dict.items():
                if key in _letters:
                    if value:
                        try:
                            attachment = Attachment.objects.get(path=value)
                            print(f"Found attachment: {attachment}")
                        except Attachment.DoesNotExist:
                            attachment = Attachment.objects.create(path=value, comments=f"Imported by {__file__}")
                            print(f"Created attachment: {attachment}")
                        attachments.append(attachment)
                else:
                    stripped_submission_dict[key] = value


            submission = Submission.objects.create(**stripped_submission_dict, applicant=applicant, contact=contact)
            submission.attachments.add(*attachments)
            # print(f"Created submission {submission}")
    else:
        print("No contact data; skipping")

    return found_report


@transaction.atomic
def main():
    args = parse_args()
    rows = load_rows(args.path)
    headers = rows[0]
    data = rows[1:]

    field_importers = []
    for header in headers:
        try:
            field_importers.append(field_map[header])
        except KeyError:
            field_importers.append(None)

    found_counts = {"applicant": 0, "contact": 0, "submission": 0}
    for row in data:
        try:
            found_report = handle_row(field_importers, row)
        except Exception as error:
            print(f"Failed to handle row: {row}")
            print(str(error))
            # raise
        else:
            found_counts["applicant"] += bool(found_report["applicant"])
            found_counts["contact"] += bool(found_report["contact"])
            found_counts["submission"] += bool(found_report["submission"])

    pprint(found_counts)

    # raise ManualRollback()


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("path")
    return parser.parse_args()


if __name__ == "__main__":
    main()
