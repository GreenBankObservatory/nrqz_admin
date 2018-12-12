#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Importer for Access Preliminary Technical Data"""

import argparse
import csv
from pprint import pprint

from tqdm import tqdm

import django

django.setup()
from django.db import transaction
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.error import GEOSException

from cases.forms import PreliminaryFacilityForm
from cases.models import (
    # Attachment,
    PreliminaryCase,
    PreliminaryFacility,
    Person,
    AlsoKnownAs,
)
from importers.access_prelim_technical.fieldmap import (
    applicant_field_mappers,
    case_field_mappers,
    facility_field_mappers,
    get_combined_field_map,
)
from importers.converters import coerce_coords


field_map = get_combined_field_map()

ACCESS_PRELIM_TECHNICAL = "access_prelim_technical"


def load_rows(path):
    with open(path, newline="", encoding="latin1") as file:
        return list(csv.reader(file))


# TODO: Consolidate, and this has been changed slightly from other
def person_is_similar_to(person, name):
    # More than 0.3 similar
    similar = Person.objects.filter(id=person.id).filter(name__trigram_similar=name)
    assert similar.count() <= 1
    # Yes, this works even if there are no items in similar
    return similar.first()


@transaction.atomic
def handle_row(field_importers, row):
    applicant_dict = {}
    prelim_facility_dict = {}
    prelim_case_dict = {}

    for fi, value in zip(field_importers, row):
        if fi:
            if fi in applicant_field_mappers:
                applicant_dict[fi.to_field] = fi.converter(value)
            elif fi in facility_field_mappers:
                try:
                    prelim_facility_dict[fi.to_field] = fi.converter(value)
                except ValueError as error:
                    tqdm.write(str(error))
                    prelim_facility_dict[fi.to_field] = None
            elif fi in case_field_mappers:
                prelim_case_dict[fi.to_field] = fi.converter(value)
            else:
                raise ValueError("Shouldn't be possible")

    found_report = dict(applicant=False, pfacility=False, pcase=False)
    pcase_num = prelim_case_dict["case_num"]
    if pcase_num is None:
        raise ValueError("case_num is None!")
    try:
        pcase = PreliminaryCase.objects.get(case_num=pcase_num)
    except PreliminaryCase.DoesNotExist:
        pcase = PreliminaryCase.objects.create(
            **prelim_case_dict, data_source=ACCESS_PRELIM_TECHNICAL
        )
        case_created = True
        found_report["pcase"] = False
    else:
        case_created = False
        found_report["pcase"] = True

    # If we found a PreliminaryCase (i.e. didn't create one),
    # and that pcase has an applicant,
    # and that applicant's name doesn't exactly match this row's,
    # then we need to handle this!
    if not case_created:
        if pcase.applicant:
            applicant_name = applicant_dict["name"]
            if pcase.applicant.name != applicant_name:
                # tqdm.write(
                #     f"Found pcase {pcase}; its applicant {pcase.applicant.name!r} differs "
                #     f"from our applicant {applicant_name!r}"
                # )
                # If the PreliminaryCase's existing Applicant is sufficiently similar to this row's,
                # then we don't need to create a new Applicant
                if person_is_similar_to(pcase.applicant, applicant_name):
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
                    if not pcase.applicant.aka.filter(
                        name=pcase.applicant.name
                    ).exists():
                        AlsoKnownAs.objects.create(
                            person=pcase.applicant,
                            name=pcase.applicant.name,
                            data_source=ACCESS_PRELIM_TECHNICAL,
                        )
                    # tqdm.write(
                    #     f"  Applicant {pcase.applicant} is now linked to names: "
                    #     f"{list(pcase.applicant.aka.values_list('name', flat=True))}"
                    # )
                    # Further, if our new applicant name is longer, then we switch
                    # to it (the assumption being that longer is better/more specific,
                    # which I've just made up)
                    if len(applicant_name) > len(pcase.applicant.name):
                        # tqdm.write(
                        #     "  Additionally, we will update this Applicant's name because the new name is longer"
                        # )
                        pcase.applicant.name = applicant_name
                        pcase.save()

                    # pcase.applicant.aka.add(name=applicant_name)
                    # Regardless
                else:
                    # TODO: Create applicant here
                    print("Not similar applicant; do something!")

    else:
        applicant = None
        if any(applicant_dict.values()):
            try:
                applicant = Person.objects.get(name=applicant_dict["name"])
                tqdm.write(f"Found applicant {applicant}")
                found_report["applicant"] = True
            except Person.DoesNotExist:
                applicant = Person.objects.create(
                    **applicant_dict, data_source=ACCESS_PRELIM_TECHNICAL
                )
                tqdm.write(f"Created applicant {applicant}")
            except Person.MultipleObjectsReturned:
                raise ValueError(applicant_dict)
        else:
            tqdm.write("No applicant data; skipping")

        pcase.applicant = applicant
        pcase.save()

    assert pcase
    if any(prelim_facility_dict.values()):

        form = PreliminaryFacilityForm(
            {
                **prelim_facility_dict,
                "case": pcase.id,
                "data_source": ACCESS_PRELIM_TECHNICAL,
            }
        )
        if form.is_valid():
            pfacility = form.save()
            # TODO: Check for PFacility existence somewhere?

            # tqdm.write(f"Created PreliminaryFacility {pfacility} <{pfacility.id}>")
        else:
            raise ValueError(form.errors.as_data())
    else:
        tqdm.write("No pfacility data; skipping")

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
            print(
                f"Error parsing {pfacility} ({pfacility.latitude}, {pfacility.longitude}): {error}"
            )
        else:
            point_str = f"Point({longitude} {latitude})"

            try:
                pfacility.location = GEOSGeometry(point_str)
                pfacility.save()
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

    found_counts = {"applicant": 0, "pfacility": 0, "pcase": 0}
    row_failures = 0
    data_with_progress = tqdm(data, unit="rows")
    for row in data_with_progress:
        try:
            found_report = handle_row(field_importers, row)
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
