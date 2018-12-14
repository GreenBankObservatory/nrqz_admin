#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Importer for Access Preliminary Technical Data"""

import argparse
import csv
from pprint import pprint

from tqdm import tqdm

import django

django.setup()
from django.contrib.postgres.search import TrigramSimilarity
from django.db import transaction
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.error import GEOSException

from cases.forms import PersonForm, PreliminaryCaseForm, PreliminaryFacilityForm
from cases.models import (
    # Attachment,
    PreliminaryCase,
    PreliminaryFacility,
    Person,
    AlsoKnownAs,
)
from importers.access_prelim_technical.fieldmap import (
    APPLICANT_FORM_MAP,
    PCASE_FORM_MAP,
    PFACILITY_FORM_MAP,
)
from importers.converters import coerce_coords


# field_map = get_combined_field_map()

ACCESS_PRELIM_TECHNICAL = "access_prelim_technical"


def load_rows(path):
    with open(path, newline="", encoding="latin1") as file:
        lines = file.readlines()

    return csv.DictReader(lines)


# TODO: Consolidate, and this has been changed slightly from other
def get_person_similarity(person, name):
    # TODO: Need to be 0.7+ similar!
    # More than 0.3 similar
    person_ = Person.objects.filter(id=person.id).annotate(
        name_similarity=TrigramSimilarity("name", name)
    )
    assert person_.count() <= 1
    return person_.first().name_similarity


def handle_pcase(row,):
    pcase_form = PCASE_FORM_MAP.render(row)
    pcase_num = pcase_form["case_num"].value()
    try:
        pcase = PreliminaryCase.objects.get(case_num=pcase_num)
    except PreliminaryCase.DoesNotExist:
        # If this doesn't work just let it blow up; that's fine
        pcase_form.save()
        pcase_created = True
    else:
        pcase_created = False

    return pcase, pcase_created


def handle_applicant(row, pcase):
    applicant_form = APPLICANT_FORM_MAP.render(row)
    if pcase.applicant:
        applicant_name = applicant_form["name"].value()
        similarity = get_person_similarity(pcase.applicant, applicant_name)
        is_similar = similarity > 0.7
        is_substring = (
            applicant_name.lower() in pcase.applicant.name.lower()
            or pcase.applicant.name.lower() in applicant_name.lower()
        )
        if is_similar or is_substring:
            # If the PreliminaryCase's existing Applicant exists and is sufficiently
            # similar to this row's, then we assume that they are the same Person.
            # We consider this safe because we are only dealing with a single Person.
            if is_similar:
                similar_str = f" is {similarity * 100:.2f}% similar to "
            else:
                similar_str = ""

            if is_substring:
                substring_str = f" is a sub- or super-string of "
            else:
                substring_str = ""

            if is_similar and is_substring:
                conjunction_str = "and"
            else:
                conjunction_str = ""
            tqdm.write(
                f"Applicant {pcase.applicant.name.strip()!r}{similar_str}{conjunction_str}"
                f"{substring_str}{applicant_name.strip()!r}; re-using"
            )

            # tqdm.write(
            #     "  However, the names are very similar, so we will link "
            #     "this new name to the existing applicant!"
            # )
            # Don't create a new AKA if one already exists for this PreliminaryCase's Applicants
            if not pcase.applicant.aka.filter(name=applicant_name).exists():
                AlsoKnownAs.objects.create(
                    person=pcase.applicant,
                    name=applicant_name,
                    data_source=ACCESS_PRELIM_TECHNICAL,
                )
            if not pcase.applicant.aka.filter(name=pcase.applicant.name).exists():
                AlsoKnownAs.objects.create(
                    person=pcase.applicant,
                    name=pcase.applicant.name,
                    data_source=ACCESS_PRELIM_TECHNICAL,
                )
            # tqdm.write(
            #     f"  Applicant {pcase.applicant} is now linked to names: "
            #     f"{list(pcase.applicant.aka.values_list('name', flat=True))}"
            # )

            # NOTE: We do not change the applicant name here -- the Access Applicant
            # DB is the source of truth for Applicant names

            return pcase.applicant, False

    applicant = applicant_form.save()
    tqdm.write(f"Created applicant {applicant}")

    # TODO: Let Person handle the addition of AKA in default case?
    pcase.applicant = applicant
    pcase.save()
    return pcase, True


def handle_pfacility(row, pcase):
    pfacility_form = PFACILITY_FORM_MAP.render(row, extra={"pcase": pcase.id})
    if pfacility_form.is_valid():
        pfacility = pfacility_form.save()
        return pfacility, True
        # TODO: Check for PFacility existence somewhere?

        # tqdm.write(f"Created PreliminaryFacility {pfacility} <{pfacility.id}>")
    else:
        raise ValueError(pfacility_form.errors.as_data())


@transaction.atomic
def handle_row(row):
    found_report = dict(applicant=False, pfacility=False, pcase=False)

    pcase, pcase_created = handle_pcase(row)
    found_report["pcase"] = pcase_created

    applicant, applicant_created = handle_applicant(row, pcase)
    found_report["applicant"] = applicant_created

    pfacility, pfacility_created = handle_pfacility(row, pcase)
    found_report["pfacility"] = pfacility_created

    return found_report


def populate_locations():
    for pfacility in tqdm(
        PreliminaryFacility.objects.filter(
            longitude__isnull=False, latitude__isnull=False, location__isnull=True
        ),
        unit="facilities",
    ):
        try:
            longitude = coerce_coords(pfacility.longitude)
            latitude = coerce_coords(pfacility.latitude)
        except ValueError as error:
            tqdm.write(
                f"Error parsing {pfacility} ({pfacility.latitude}, {pfacility.longitude}): {error}"
            )
        else:
            point_str = f"Point({longitude} {latitude})"

            try:
                pfacility.location = GEOSGeometry(point_str)
                pfacility.save()
            except GEOSException as error:
                tqdm.write(f"Error saving {point_str}: {error}")


@transaction.atomic
def main():
    args = parse_args()
    rows = list(load_rows(args.path))
    found_counts = {"applicant": 0, "pfacility": 0, "pcase": 0}
    row_failures = 0
    for row in tqdm(rows, unit="rows"):
        try:
            found_report = handle_row(row)
        except Exception as error:
            if not args.durable:
                raise
            tqdm.write(f"Failed to handle row: {row}")
            tqdm.write(str(error))
            row_failures += 1
        else:
            found_counts["applicant"] += bool(found_report["applicant"])
            found_counts["pcase"] += bool(found_report["pcase"])
            found_counts["pfacility"] += bool(found_report["pfacility"])

    pprint(found_counts)
    tqdm.write(f"Failed rows: {row_failures}")
    tqdm.write(f"Total rows: {len(data)}")

    populate_locations()

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
