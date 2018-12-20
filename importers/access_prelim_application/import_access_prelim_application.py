#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Importer for Access Preliminary Applicant Data"""


import argparse
import csv
from pprint import pprint
import re

import django

django.setup()
from django.db import transaction

from tqdm import tqdm

from cases.models import Attachment, Case, PreliminaryCase, PreliminaryCaseGroup, Person
from importers.access_prelim_application.fieldmap import (
    APPLICANT_FORM_MAP,
    CONTACT_FORM_MAP,
    PCASE_FORM_MAP,
    ATTACHMENT_FORM_MAPS,
)

from utils.constants import ACCESS_PRELIM_APPLICATION
from utils.read_access_csv import load_rows

# https://regex101.com/r/g6NM6e/1
case_regex_str = r"(?:(?:NRQZ ID )|(?:NRQZ#)|(?:Case\s*))(?P<case_num>\d+)"
case_regex = re.compile(case_regex_str, re.IGNORECASE)

pcase_regex_str = r"NRQZ#P(\d+)"
pcase_regex = re.compile(pcase_regex_str, re.IGNORECASE)


def derive_case_num(pcase):
    m = case_regex.search(pcase.comments)
    if m:
        case_num = int(m.groupdict()["case_num"])
    else:
        case_num = None

    return case_num


def derive_related_pcases(pcase):
    m = pcase_regex.findall(pcase.comments)
    if m:
        pcase_nums = [int(pcase_num) for pcase_num in m]
    else:
        pcase_nums = []

    return pcase_nums


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
def handle_pcase(row):
    pcase_form = PCASE_FORM_MAP.render(row)
    pcase_num = pcase_form["case_num"].value()
    if PreliminaryCase.objects.filter(case_num=pcase_num).exists():
        pcase = PreliminaryCase.objects.get(case_num=pcase_num)
        pcase_created = False
        tqdm.write(f"Found pcase {pcase}")
    else:
        pcase = PCASE_FORM_MAP.save(pcase_form)
        tqdm.write(f"Created pcase {pcase}")
        pcase_created = True

    return pcase, pcase_created


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
    found_report = dict(applicant=False, contact=False, pcase=False)

    pcase, pcase_created = handle_pcase(row)
    applicant, applicant_created = handle_applicant(row, pcase)
    contact, contact_created = handle_contact(row, pcase)
    attachments = handle_attachments(row, pcase)
    return found_report


def derive_stuff():
    for pcase in tqdm(PreliminaryCase.objects.all(), unit="cases"):
        case_num = derive_case_num(pcase)
        if case_num:
            if pcase.case and pcase.case.case_num != case_num:
                raise ValueError("aw man")
            try:
                pcase.case = Case.objects.get(case_num=case_num)
            except Case.DoesNotExist:
                tqdm.write(
                    f"Found case ID {case_num} in PCase {pcase} comments, but no matching Case found"
                )
                tqdm.write(pcase.comments)
                tqdm.write("\n")
            else:
                tqdm.write(
                    f"Successfully derived case {pcase.case} from {pcase} comments"
                )

        related_pcase_nums = derive_related_pcases(pcase)
        if related_pcase_nums:
            related_pcases = PreliminaryCase.objects.filter(
                case_num__in=related_pcase_nums
            )
            if len(related_pcases) != len(related_pcase_nums):
                diff = set(related_pcase_nums).difference(
                    set([pid for pid in related_pcases.all()])
                )
                tqdm.write(
                    f"One or more PreliminaryCases not found! Failed to find: {diff}"
                )

            existing_pcase_groups = (
                related_pcases.order_by("pcase_group")
                .values_list("pcase_group", flat=True)
                .distinct()
            )
            existing_pcase_groups = [g for g in existing_pcase_groups if g]
            if len(existing_pcase_groups) == 0:
                pcase.pcase_group = PreliminaryCaseGroup.objects.create(
                    data_source=ACCESS_PRELIM_APPLICATION
                )
                tqdm.write(f"Created PCG {pcase.pcase_group}")
            elif len(existing_pcase_groups) == 1:
                pcase.pcase_group = PreliminaryCaseGroup.objects.get(
                    id=existing_pcase_groups[0]
                )
                tqdm.write(f"Found PCG {pcase.pcase_group}")
                pcase.save()
            else:
                raise ValueError("fdfskfjasdl")

            for related_pcase in related_pcases.all():
                if (
                    not related_pcase.pcase_group
                    or related_pcase.pcase_group == pcase.pcase_group
                ):
                    related_pcase.pcase_group = pcase.pcase_group
                    related_pcase.save()
                else:
                    raise ValueError("Oh shit")

            tqdm.write(
                f"PCG {pcase.pcase_group} now contains pcases: {pcase.pcase_group.prelim_cases.all()}"
            )
        else:
            pcase.pcase_group = PreliminaryCaseGroup.objects.create(
                data_source=ACCESS_PRELIM_APPLICATION
            )
            pcase.save()

        if case_num or related_pcase_nums:
            pcase.save()


@transaction.atomic
def main():
    args = parse_args()
    rows = list(load_rows(args.path))

    found_counts = {"applicant": 0, "contact": 0, "pcase": 0}
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
            found_counts["pcase"] += bool(found_report["pcase"])

    derive_stuff()

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
    parser.add_argument(
        "-D", "--durable", action="store_true", help=("Continue past row errors")
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
