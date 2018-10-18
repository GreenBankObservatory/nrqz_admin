#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""docstring"""


import argparse
import csv
from pprint import pprint

import django

django.setup()
from django.db import transaction

from tqdm import tqdm

from cases.models import Attachment, Case, Person
from tools.accessfieldmap import (
    applicant_field_mappers,
    contact_field_mappers,
    case_field_mappers,
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
    case_dict = {}

    for fi, value in zip(field_importers, row):
        if fi:
            if fi in applicant_field_mappers:
                applicant_dict[fi.to_field] = fi.converter(value)
            elif fi in contact_field_mappers:
                contact_dict[fi.to_field] = fi.converter(value)
            elif fi in case_field_mappers:
                case_dict[fi.to_field] = fi.converter(value)
            else:
                raise ValueError("Shouldn't be possible")

    found_report = dict(applicant=False, contact=False, case=False)
    applicant = None
    if any(applicant_dict.values()):
        try:
            applicant = Person.objects.get(name=applicant_dict["name"])
            tqdm.write(f"Found applicant {applicant}")
            found_report["applicant"] = True
        except Person.DoesNotExist:
            applicant = Person.objects.create(**applicant_dict)
            # tqdm.write(f"Created applicant {applicant}")
        except Person.MultipleObjectsReturned:
            raise ValueError(applicant_dict)
    else:
        tqdm.write("No applicant data; skipping")

    contact = None
    if any(contact_dict.values()):
        try:
            contact = Person.objects.get(name=contact_dict["name"])
            tqdm.write(f"Found contact {contact}")
            found_report["contact"] = True
        except Person.DoesNotExist:
            contact = Person.objects.create(**contact_dict)
            # tqdm.write(f"Created contact {contact}")
        except Person.MultipleObjectsReturned:
            raise ValueError(contact_dict)
    else:
        tqdm.write("No contact data; skipping")

    if any(case_dict.values()):
        try:
            case = Case.objects.get(case_num=case_dict["case_num"])
            tqdm.write(f"Found case {case}")
            found_report["case"] = True
        except Case.DoesNotExist:

            stripped_case_dict = {}
            attachments = []
            for key, value in case_dict.items():
                if key in _letters:
                    if value:
                        try:
                            attachment = Attachment.objects.get(path=value)
                            tqdm.write(f"Found attachment: {attachment}")
                        except Attachment.DoesNotExist:
                            attachment = Attachment.objects.create(path=value, comments=f"Imported by {__file__}")
                            tqdm.write(f"Created attachment: {attachment}")
                        attachments.append(attachment)
                else:
                    stripped_case_dict[key] = value


            case = Case.objects.create(**stripped_case_dict, applicant=applicant, contact=contact)
            case.attachments.add(*attachments)
            # tqdm.write(f"Created case {case}")
    else:
        tqdm.write("No contact data; skipping")

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

    found_counts = {"applicant": 0, "contact": 0, "case": 0}
    data_with_progress = tqdm(data, unit="rows")
    for row in data_with_progress:
        try:
            found_report = handle_row(field_importers, row)
        except Exception as error:
            tqdm.write(f"Failed to handle row: {row}")
            tqdm.write(str(error))
            # raise
        else:
            found_counts["applicant"] += bool(found_report["applicant"])
            found_counts["contact"] += bool(found_report["contact"])
            found_counts["case"] += bool(found_report["case"])

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
