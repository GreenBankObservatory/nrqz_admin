from collections import OrderedDict
import argparse
import json
import re
import string

from tqdm import tqdm

from django.contrib.postgres.search import TrigramSimilarity
from django_import_data import BaseImportCommand

from cases.models import Person
from tools.merge_objects import merge_model_objects

THRESHOLD_DEFAULT = 0.7

CONCRETE_PERSON_FIELDS = (
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
)
PERSON_FIELD_WHITELIST = [
    Person._meta.get_field(name)
    for name in (*CONCRETE_PERSON_FIELDS, "applicant_for_cases", "contact_for_cases")
]


class Command(BaseImportCommand):

    help = "Merge Person objects together"

    def add_arguments(self, parser):
        parser.add_argument("-i", "--input")
        parser.add_argument("-o", "--output")
        parser.add_argument(
            "-t",
            "--threshold",
            default=THRESHOLD_DEFAULT,
            help="The threshold for which names are considered a match",
        )
        parser.add_argument(
            "-l",
            "--limit",
            type=float,
            help="Specify a random percentage [0.0 - 1.0] of rows that should be processed",
        )

    def handle(self, *args, **options):
        if options["input"]:
            people_ids_to_merge = self.load(options["input"])
        else:
            people_ids_to_merge = self.find_similar_people(
                threshold=options["threshold"], limit=options["limit"]
            )

        if options["output"]:
            self.dump(people_ids_to_merge, options["output"])

        # Get Person object for each Person ID in each group
        people_to_merge = [
            Person.objects.filter(id__in=group).order_by("name")
            for group in people_ids_to_merge
        ]

        merge_summary = OrderedDict(
            (("naive", []), ("only_names", []), ("names_and_fields", []))
        )

        # print("Summary of merge groups:")
        for group in people_to_merge:
            unique_names = group.values_list("name", flat=True).distinct()
            # print(f"--- Group ({unique_names.count()} unique names): ---")
            # for name in unique_names:
            #     print(f"  {name}")
            # print("Unique, non-null field values")
            unique_fields = {}
            for fdict in group.values(*CONCRETE_PERSON_FIELDS[1:]).distinct():
                for field, value in fdict.items():
                    if value:
                        if field in unique_fields:
                            unique_fields[field].add(value)
                        else:
                            unique_fields[field] = {value}
            fields_to_merge = {
                field: values
                for field, values in unique_fields.items()
                if len(values) > 1
            }

            if fields_to_merge:
                category = "names_and_fields"
            else:
                if unique_names.count() == 1:
                    category = "naive"
                else:
                    category = "only_names"

            merge_summary[category].append(
                {
                    "group": group,
                    "unique_names": unique_names,
                    # "unique_fields": unique_fields,
                    "unique_fields": fields_to_merge,
                }
            )

        print("=" * 80)
        print("Summary of merge categories:")
        print(f"  Can be naively merged: {len(merge_summary['naive'])}")
        print(
            f"  Names need merging, but other fields can be naively merged: {len(merge_summary['only_names'])}"
        )
        print(
            f"  Names and one or more other fields need merging: {len(merge_summary['names_and_fields'])}"
        )
        print("=" * 80)
        for category, summaries in merge_summary.items():
            if category != "naive":
                print(f"Category: {category}")
                for summary in summaries:
                    print(f"--- Group: ---")
                    print("Unique names:")
                    print(summary["unique_names"])
                    print("Unique fields:")
                    print(summary["unique_fields"])
                    print("-" * 80)

        self.merge_people([ms["group"] for ms in merge_summary["naive"]])

    def count_populated_fields(self, instance):
        return sum(
            [bool(field.value_to_string(instance)) for field in instance._meta.fields]
        )

    def merge_people(self, people_to_merge):
        for people_group in people_to_merge:
            print("The following people will be merged together:")
            person_to_keep = people_group.first()
            max_populated_fields = self.count_populated_fields(person_to_keep)
            for person in people_group:
                populated_fields = self.count_populated_fields(person)
                tqdm.write(
                    f"  {person.name!r} (id: {person.id}) [pop. fields: {populated_fields}]"
                )
                if populated_fields > max_populated_fields:
                    person_to_keep = person

            merge_model_objects(
                person_to_keep,
                list(people_group.exclude(id=person_to_keep.id)),
                field_whitelist=PERSON_FIELD_WHITELIST,
            )

    def find_similar_people(self, threshold=THRESHOLD_DEFAULT, limit=None):
        people = Person.objects.all()
        if limit is not None:
            num_people = people.count() * limit
            people = Person.objects.filter(id__lt=num_people)
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
                .annotate(similarity=TrigramSimilarity("name__unaccent", name))
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

    def dump(self, people_ids_to_merge, path, **kwargs):
        with open(path, "w") as file:
            json.dump(list(people_ids_to_merge), file, **kwargs)
            # json.dump([list(group.values_list("id", flat=True)) for group in people_ids_to_merge], file)

    def load(self, path, **kwargs):
        with open(path) as file:
            people_ids_to_merge = json.load(file, **kwargs)
            return people_ids_to_merge

    def compare_thresholds(self, thresholds):
        print(f"Thresholds: {thresholds}")
        for threshold in thresholds:
            groups = self.find_similar_people(threshold=threshold)
            self.dump(groups, f"people_t={threshold}.json")
