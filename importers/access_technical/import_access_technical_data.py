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
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.error import GEOSException

from tqdm import tqdm

from cases.forms import FacilityForm
from cases.models import Attachment, Case, Facility, Person, AlsoKnownAs
from importers.access_technical.fieldmap import (
    applicant_field_mappers,
    facility_field_mappers,
    get_combined_field_map,
    coerce_coords,
)


field_map = get_combined_field_map()

ACCESS_TECHNICAL = "access_technical"


class ManualRollback(Exception):
    pass


def load_rows(path):
    with open(path, newline="", encoding="latin1") as file:
        return list(csv.reader(file))


# def handle_applicant(name):


def person_is_similar_to(person, name):
    # More than 0.3 similar
    similar = Person.objects.filter(id=person.id).filter(name__trigram_similar=person)
    assert similar.count() <= 1
    # Yes, this works even if there are no items in similar
    return similar.first()


@transaction.atomic
def handle_row(field_importers, row):
    applicant_dict = {}
    facility_dict = {}

    for fi, value in zip(field_importers, row):
        if fi:
            if fi in applicant_field_mappers:
                applicant_dict[fi.to_field] = fi.converter(value)
            elif fi in facility_field_mappers:
                try:
                    facility_dict[fi.to_field] = fi.converter(value)
                except ValueError as error:
                    tqdm.write(str(error))
                    facility_dict[fi.to_field] = None

            else:
                raise ValueError("Shouldn't be possible")

    found_report = dict(applicant=False, facility=False, case=False)

    case_num = facility_dict.pop("case_num")
    if case_num is None:
        raise ValueError("Null case_num!")

    try:
        case = Case.objects.get(case_num=case_num)
    except Case.DoesNotExist:
        case = Case.objects.create(case_num=case_num, data_source=ACCESS_TECHNICAL)
        case_created = True
        found_report["case"] = False
    else:
        case_created = False
        found_report["case"] = True

    # If we found a Case (i.e. didn't create one),
    # and that case has an applicant,
    # and that applicant's name doesn't exactly match this row's,
    # then we need to handle this!
    if not case_created:
        if case.applicant:
            applicant_name = applicant_dict["name"]
            if case.applicant.name != applicant_name:
                tqdm.write(
                    f"Found case {case}; its applicant {case.applicant.name!r} differs "
                    f"from our applicant {applicant_name!r}"
                )
                # If the Case's existing Applicant is sufficiently similar to this row's,
                # then we don't need to create a new Applicant
                if person_is_similar_to(case.applicant, applicant_name):
                    tqdm.write(
                        "  However, the names are very similar, so we will link "
                        "this new name to the existing applicant!"
                    )
                    # Don't create a new AKA if one already exists for this Case's Applicants
                    if not case.applicant.aka.filter(name=applicant_name).exists():
                        AlsoKnownAs.objects.create(
                            person=case.applicant,
                            name=applicant_name,
                            data_source=ACCESS_TECHNICAL,
                        )
                    if not case.applicant.aka.filter(name=case.applicant.name).exists():
                        AlsoKnownAs.objects.create(
                            person=case.applicant,
                            name=case.applicant.name,
                            data_source=ACCESS_TECHNICAL,
                        )
                    tqdm.write(
                        f"  Applicant {case.applicant} is now linked to names: "
                        f"{list(case.applicant.aka.values_list('name', flat=True))}"
                    )
                    # Further, if our new applicant name is longer, then we switch
                    # to it (the assumption being that longer is better/more specific,
                    # which I've just made up)
                    if len(applicant_name) > len(case.applicant.name):
                        tqdm.write(
                            "  Additionally, we will update this Applicant's name because the new name is longer"
                        )
                        case.applicant.name = applicant_name
                        case.save()

                    # case.applicant.aka.add(name=applicant_name)
                    # Regardless
                else:
                    # TODO: Create applicant here
                    pass
                    raise ValueError("balls")

    else:
        applicant = None
        if any(applicant_dict.values()):
            try:
                applicant = Person.objects.get(name=applicant_dict["name"])
                tqdm.write(f"Found applicant {applicant}")
                found_report["applicant"] = True
            except Person.DoesNotExist:
                applicant = Person.objects.create(
                    **applicant_dict, data_source=ACCESS_TECHNICAL
                )
                tqdm.write(f"Created applicant {applicant}")
            except Person.MultipleObjectsReturned:
                raise ValueError(applicant_dict)
        else:
            tqdm.write("No applicant data; skipping")
            pass

        case.applicant = applicant
        case.save()

    assert case
    if any(facility_dict.values()):
        stripped_facility_dict = {}
        for key, value in facility_dict.items():
            stripped_facility_dict[key] = value

        form = FacilityForm(
            {**stripped_facility_dict, "case": case.id, "data_source": ACCESS_TECHNICAL}
        )
        if form.is_valid():
            facility = form.save()
            # tqdm.write(f"Created Facility {facility} <{facility.id}>")
        else:
            raise ValueError(form.errors.as_data())
    else:
        tqdm.write("No facility data; skipping")

    return found_report


def populate_locations():
    for facility in tqdm(
        Facility.objects.filter(
            longitude__isnull=False, latitude__isnull=False, location__isnull=True
        ),
        unit="facilities",
    ):
        try:
            longitude = coerce_coords(facility.longitude)
            latitude = coerce_coords(facility.latitude)
        except ValueError as error:
            print(
                f"Error parsing {facility} ({facility.latitude}, {facility.longitude}): {error}"
            )
        else:
            point_str = f"Point({longitude} {latitude})"

            try:
                facility.location = GEOSGeometry(point_str)
                facility.save()
            except GEOSException as error:
                print(f"Error saving {point_str}: {error}")


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

    found_counts = {"applicant": 0, "facility": 0, "case": 0}
    row_failures = 0
    data_with_progress = tqdm(data, unit="rows")
    for row in data_with_progress:
        try:
            found_report = handle_row(field_importers, row)
        except Exception as error:
            tqdm.write(f"Failed to handle row: {row}")
            tqdm.write(str(error))
            if not args.durable:
                raise
            row_failures += 1
        else:
            found_counts["applicant"] += bool(found_report["applicant"])
            found_counts["case"] += bool(found_report["case"])
            found_counts["facility"] += bool(found_report["facility"])

    pprint(found_counts)
    print(f"Failed rows: {row_failures}")
    print(f"Total rows: {len(data)}")

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
