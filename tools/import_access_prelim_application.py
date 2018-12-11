#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""docstring"""


import argparse
import csv
from pprint import pprint
import re

import django

django.setup()
from django.db import transaction

from tqdm import tqdm

from cases.models import Attachment, Case, PreliminaryCase, PreliminaryCaseGroup, Person
from tools.prelim_accessfieldmap import (
    applicant_field_mappers,
    contact_field_mappers,
    case_field_mappers,
    get_combined_field_map,
)

field_map = get_combined_field_map()

ACCESS_PRELIM_APPLICATION = "access_prelim_application"


class ManualRollback(Exception):
    pass


def load_rows(path):
    with open(path, newline="", encoding="latin1") as file:
        return list(csv.reader(file))


_letters = [f"letter{i}" for i in range(1, 9)]

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

    found_report = dict(applicant=False, contact=False, pcase=False)
    applicant = None
    if any(applicant_dict.values()):
        try:
            applicant = Person.objects.get(name=applicant_dict["name"])
            # tqdm.write(f"Found applicant {applicant}")
            found_report["applicant"] = True
        except Person.DoesNotExist:
            applicant = Person.objects.create(
                **applicant_dict, data_source=ACCESS_PRELIM_APPLICATION
            )
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
            contact = Person.objects.create(
                **contact_dict, data_source=ACCESS_PRELIM_APPLICATION
            )
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
                            path=value,
                            comments=f"Imported by {__file__}",
                            data_source=ACCESS_PRELIM_APPLICATION,
                        )
                        # tqdm.write(f"Created attachment: {attachment}")
                    attachments.append(attachment)
            else:
                stripped_case_dict[key] = value

        try:
            pcase = PreliminaryCase.objects.get(case_num=case_dict["case_num"])
            pcase.applicant = applicant
            pcase.contact = contact
            pcase.save()
            tqdm.write(f"Found Pcase {pcase}")
            found_report["pcase"] = True
        except PreliminaryCase.DoesNotExist:
            pcase = PreliminaryCase.objects.create(
                **stripped_case_dict,
                applicant=applicant,
                contact=contact,
                data_source=ACCESS_PRELIM_APPLICATION,
            )
            # tqdm.write(f"Created pcase {pcase}")

        pcase.attachments.add(*attachments)
    else:
        tqdm.write("No pcase data; skipping")

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
        "pcase": 0,
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
            found_counts["pcase"] += bool(found_report["pcase"])
            if (
                not (found_report["applicant"] or found_report["contact"])
                and found_report["pcase"]
            ):
                found_counts["technical_with_no_case"] += 1

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
    return parser.parse_args()


if __name__ == "__main__":
    main()
