#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Importer for Access Applicant Data"""


import argparse
from pprint import pprint


import django
from django.db import transaction

django.setup()

from tqdm import tqdm

from cases.models import Attachment, Case
from importers.access_application.fieldmap import (
    APPLICANT_FORM_MAP,
    CONTACT_FORM_MAP,
    CASE_FORM_MAP,
    ATTACHMENT_FORM_MAPS,
)
from utils.read_access_csv import load_rows


# TODO: MERGE
def handle_applicant(row, case):
    applicant = APPLICANT_FORM_MAP.save(row)
    # tqdm.write(f"Created applicant {applicant}")
    case.applicant = applicant
    case.save()

    return applicant, True


# TODO: MERGE
def handle_contact(row, case):
    contact = CONTACT_FORM_MAP.save(row)
    # tqdm.write(f"Created contact {contact}")
    case.contact = contact
    case.save()

    return contact, True


# TODO: MERGE
def handle_case(row):
    case_form = CASE_FORM_MAP.render(row)
    case_num = case_form["case_num"].value()
    if Case.objects.filter(case_num=case_num).exists():
        case = Case.objects.get(case_num=case_num)
        case_created = False
        tqdm.write(f"Found case {case}")
    else:
        case = CASE_FORM_MAP.save(case_form)
        tqdm.write(f"Created case {case}")
        case_created = True

    return case, case_created


# TODO: MERGE
def handle_attachments(row, case):
    attachments = []
    for form_map in ATTACHMENT_FORM_MAPS:
        attachment_form = form_map.render(
            row, extra={"comments": f"Imported by {__file__}"}
        )
        path = attachment_form["path"].value()
        if path:
            if Attachment.objects.filter(path=path).exists():
                attachment = Attachment.objects.get(path=path)
            else:
                attachment = form_map.save(attachment_form)

            attachments.append(attachment)
            case.attachments.add(attachment)
    return attachments


@transaction.atomic
def handle_row(row):
    found_report = dict(applicant=False, contact=False, case=False)

    case, case_created = handle_case(row)
    found_report["case"] = case_created

    applicant, applicant_created = handle_applicant(row, case)
    found_report["applicant"] = applicant_created

    contact, contact_created = handle_contact(row, case)
    found_report["contact"] = contact_created

    attachments = handle_attachments(row, case)
    return found_report


@transaction.atomic
def main():
    args = parse_args()
    rows = list(load_rows(args.path))

    found_counts = {"applicant": 0, "contact": 0, "case": 0}
    for row in tqdm(rows, unit="rows"):
        try:
            found_report = handle_row(row)
        except Exception as error:
            tqdm.write(f"Failed to handle row: {row}")
            if not args.durable:
                raise error
            tqdm.write(str(error))
        else:
            found_counts["applicant"] += bool(found_report["applicant"])
            found_counts["contact"] += bool(found_report["contact"])
            found_counts["case"] += bool(found_report["case"])

    pprint(found_counts)

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
