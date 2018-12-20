#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Importer for Access Technical Data"""


import argparse
from pprint import pprint

from django.db import transaction
import django

django.setup()

from tqdm import tqdm

from cases.models import Case
from importers.access_technical.fieldmap import (
    APPLICANT_FORM_MAP,
    CASE_FORM_MAP,
    FACILITY_FORM_MAP,
)
from utils.read_access_csv import load_rows


def handle_case(row):
    case_form = CASE_FORM_MAP.render(row)
    case_num = case_form["case_num"].value()
    if Case.objects.filter(case_num=case_num).exists():
        case = Case.objects.get(case_num=case_num)
        tqdm.write(f"Found case {case}")
        case_created = False
    else:
        case = case_form.save()
        tqdm.write(f"Created case {case}")
        case_created = True

    return case, case_created


def handle_applicant(row, case):
    applicant = APPLICANT_FORM_MAP.save(row)
    tqdm.write(f"Created applicant {applicant}")
    case.applicant = applicant
    case.save()
    return applicant, True


def handle_facility(row, case):
    facility = FACILITY_FORM_MAP.save(row, extra={"case": case.id})
    tqdm.write(f"Created facility {facility}")
    return facility, True


def handle_row(row):
    found_report = dict(applicant=False, facility=False, case=False)

    case, case_created = handle_case(row)
    found_report["case"] = case_created

    applicant, applicant_created = handle_applicant(row, case)
    found_report["applicant"] = applicant_created

    facility, facility_created = handle_facility(row, case)
    found_report["facility"] = facility_created

    return found_report


@transaction.atomic
def main():
    args = parse_args()
    rows = list(load_rows(args.path))

    found_counts = {"applicant": 0, "facility": 0, "case": 0}
    row_failures = 0
    for row in tqdm(rows, unit="rows"):
        try:
            found_report = handle_row(row)
        except Exception as error:
            tqdm.write(f"Failed to handle row: {row}")
            if not args.durable:
                raise
            tqdm.write(str(error))
            row_failures += 1
        else:
            found_counts["applicant"] += bool(found_report["applicant"])
            found_counts["case"] += bool(found_report["case"])
            found_counts["facility"] += bool(found_report["facility"])

    pprint(found_counts)
    print(f"Failed rows: {row_failures}")
    print(f"Total rows: {len(rows)}")

    if args.dry_run:
        tqdm.write("Dry run; rolling back now(ish)")
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
    parser.add_argument(
        "-D", "--durable", action="store_true", help=("Continue past row errors")
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
