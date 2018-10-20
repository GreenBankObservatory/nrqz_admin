#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""docstring"""


import argparse
import json
import string
import re

import django

django.setup()
from django.contrib.postgres.search import TrigramSimilarity

from tqdm import tqdm

from cases.models import Person
from tools.merge_objects import merge_model_objects

THRESHOLD_DEFAULT = 0.7

person_field_whitelist = [
    Person._meta.get_field(name)
    for name in (
        "name",
        "phone",
        "fax",
        "email",
        "street",
        "city",
        "county",
        "state",
        "zipcode",
        "comments",
        "applicant_for_cases",
        "contact_for_cases",
    )
]


def count_populated_fields(instance):
    return sum(
        [bool(field.value_to_string(instance)) for field in instance._meta.fields]
    )


def clean_name(name):
    clean_value = re.sub(f"[{string.punctuation}]", "", name)
    if clean_value != name:
        tqdm.write(f"{name!r} is now {clean_value!r}")
    return clean_value


def merge_people(people_to_merge):
    for people_group in people_to_merge:
        print("The following people will be merged together:")
        person_to_keep = people_group.first()
        max_populated_fields = count_populated_fields(person_to_keep)
        for person in people_group:
            populated_fields = count_populated_fields(person)
            tqdm.write(
                f"  {person.name!r} (id: {person.id}) [pop. fields: {populated_fields}]"
            )
            if populated_fields > max_populated_fields:
                person_to_keep = person

        merge_model_objects(
            person_to_keep,
            list(people_group.exclude(id=person_to_keep.id)),
            field_whitelist=person_field_whitelist,
        )


def find_similar_people(threshold=THRESHOLD_DEFAULT):
    people = Person.objects.all()
    # people = Person.objects.filter(id__lt=1000)
    tqdm.write(f"Processing {len(people)} people")

    # A list of lists of the IDs of Person objects that need to be merged together
    people_ids_to_merge = []
    processed = set()
    for name in tqdm(people.values_list("name", flat=True), unit="people"):
        similar_people = (
            # We must exclude any people that have already been processed, because
            # this means they are already in people_ids_to_merge. If we didn't
            # exclude them here, we would get duplicates in people_ids_to_merge
            people.exclude(id__in=processed)
            # Annotate each item with its similarity ranking with the current name
            .annotate(similarity=TrigramSimilarity("name", name))
            # And filter out anything below the given threshold
            .filter(similarity__gt=threshold)
        )
        num_similar_people = similar_people.count()
        if num_similar_people > 1:
            tqdm.write(f"Found {num_similar_people} names similar to {name!r}")
            # for similar_person in similar_people.all():
            #     tqdm.write(f"  {similar_person.name!r} (id: {similar_person.id})")

            ids = list(similar_people.values_list("id", flat=True))
            people_ids_to_merge.append(ids)
            processed.update(ids)

    return people_ids_to_merge


def dump(people_ids_to_merge, path, **kwargs):
    with open(path, "w") as file:
        json.dump(list(people_ids_to_merge), file, **kwargs)
        # json.dump([list(group.values_list("id", flat=True)) for group in people_ids_to_merge], file)


def load(path, **kwargs):
    with open(path) as file:
        people_ids_to_merge = json.load(file, **kwargs)
        return people_ids_to_merge

def compare_thresholds(thresholds):
    print(f"Thresholds: {thresholds}")
    for threshold in thresholds:
        groups = find_similar_people(threshold=threshold)
        dump(groups, f"people_t={threshold}.json")

def main():
    args = parse_args()
    if args.input:
        people_ids_to_merge = load(args.input)
    else:
        people_ids_to_merge = find_similar_people(threshold=args.threshold)

    if args.output:
        dump(people_ids_to_merge, args.output)

    # Get Person object for each Person ID in each group
    people_to_merge = [
        Person.objects.filter(id__in=group) for group in people_ids_to_merge
    ]

    print("Summary of unique names:")
    for person in sorted([group[0].name for group in people_to_merge]):
        print(f"  {person}")
    # print(people_to_merge)
    # merge_people(people_to_merge)


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("-i", "--input")
    parser.add_argument("-o", "--output")
    parser.add_argument(
        "-t",
        "--threshold",
        default=THRESHOLD_DEFAULT,
        help="The threshold for which names are considered a match",
    )

    return parser.parse_args()


if __name__ == "__main__":
    # main()
    compare_thresholds([i / 10 for i in range(1, 10)])
