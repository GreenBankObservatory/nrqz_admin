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

from cases.models import Attachment, PreliminaryCase, Person
from tools.prelim_accessfieldmap import (
    applicant_field_mappers,
    contact_field_mappers,
    case_field_mappers,
    get_combined_field_map,
)

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
            # tqdm.write(f"Found applicant {applicant}")
            found_report["applicant"] = True
        except Person.DoesNotExist:
            applicant = Person.objects.create(**applicant_dict)
            # tqdm.write(f"Created applicant {applicant}")
        except Person.MultipleObjectsReturned:
            raise ValueError(applicant_dict)
    else:
        # tqdm.write("No applicant data; skipping")
        pass

    contact = None
    if any(contact_dict.values()):
        try:
            contact = Person.objects.get(name=contact_dict["name"])
            # tqdm.write(f"Found contact {contact}")
            found_report["contact"] = True
        except Person.DoesNotExist:
            contact = Person.objects.create(**contact_dict)
            # tqdm.write(f"Created contact {contact}")
        except Person.MultipleObjectsReturned:
            raise ValueError(contact_dict)
    else:
        # tqdm.write("No contact data; skipping")
        pass

    if any(case_dict.values()):
        stripped_case_dict = {}
        attachments = []
        for key, value in case_dict.items():
            if key in _letters:
                if value:
                    try:
                        attachment = Attachment.objects.get(path=value)
                        # tqdm.write(f"Found attachment: {attachment}")
                    except Attachment.DoesNotExist:
                        attachment = Attachment.objects.create(
                            path=value, comments=f"Imported by {__file__}"
                        )
                        # tqdm.write(f"Created attachment: {attachment}")
                    attachments.append(attachment)
            else:
                stripped_case_dict[key] = value

        try:
            case = PreliminaryCase.objects.get(case_num=case_dict["case_num"])
            case.applicant = applicant
            case.contact = contact
            case.save()
            tqdm.write(f"Found case {case}")
            found_report["case"] = True
        except PreliminaryCase.DoesNotExist:
            case = PreliminaryCase.objects.create(
                **stripped_case_dict, applicant=applicant, contact=contact
            )
            tqdm.write(f"Created case {case}")

        case.attachments.add(*attachments)
    else:
        tqdm.write("No case data; skipping")

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

    found_counts = {
        "applicant": 0,
        "contact": 0,
        "case": 0,
        "technical_with_no_case": 0,
    }
    data_with_progress = tqdm(data, unit="rows")
    for row in data_with_progress:
        try:
            found_report = handle_row(field_importers, row)
        except Exception as error:
            tqdm.write(f"Failed to handle row: {row}")
            tqdm.write(str(error))
            # raise
            pass
        else:
            found_counts["applicant"] += bool(found_report["applicant"])
            found_counts["contact"] += bool(found_report["contact"])
            found_counts["case"] += bool(found_report["case"])
            if (
                not (found_report["applicant"] or found_report["contact"])
                and found_report["case"]
            ):
                found_counts["technical_with_no_case"] += 1

    pprint(found_counts)

    if args.dry_run:
        print("Dry run; rolling back now(ish)")
        transaction.set_rollback(True)


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("path")
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help=(
            "Roll back all database changes after execution. Note that "
            "this will leave gaps in the PKs where created objects were rolled back"
        ),
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
