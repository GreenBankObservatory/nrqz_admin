"""Merge People together!"""

from pprint import pformat
import json

from tqdm import tqdm

from django.db import transaction

from django_import_data import BaseImportCommand

from cases.models import Person
from utils.merge_people import find_similar_people, merge_people

THRESHOLD_DEFAULT = 0.9


def proportion(value):
    value = float(value)
    if not 0 < value <= 1:
        raise ValueError("Value out of range")
    return value


class Command(BaseImportCommand):

    help = "Merge Person objects together"

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "-i",
            "--input",
            help="The path to an input JSON file, as created by --output",
        )
        group.add_argument(
            "-t",
            "--threshold",
            type=proportion,
            default=THRESHOLD_DEFAULT,
            help="The threshold for which names are considered a match (based "
            "on trigram similarity). Value of '1' means exact matches only",
        )
        parser.add_argument("--merge", action="store_true", help="Merge people")
        parser.add_argument(
            "-o",
            "--output",
            help="The path to an output JSON file. This is a list of model groups, "
            "where each model group is a list of IDs. e.g. [[1,2,3],[4,5,6]]. This "
            "can be used by --input, and is helpful for testing because it "
            "avoids the need to re-create merge groups (the most expensive part "
            "of the process)",
        )

        parser.add_argument(
            "-l",
            "--limit",
            type=proportion,
            help="Specify a random percentage [0.0 - 1.0] of rows that should be processed",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do everything as normal, but roll back all database changes at the end.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["input"]:
            people_ids_to_merge = self.load(options["input"])
        elif options["threshold"]:
            people_ids_to_merge = self.build_merge_groups(
                threshold=options["threshold"], limit=options["limit"]
            )
        else:
            raise ValueError("You must specify either 'input' or 'threshold'")

        if options["output"]:
            self.dump(people_ids_to_merge, options["output"])

        tqdm.write("Getting people instances...")
        # Get Person object for each Person ID in each group
        # people_ids_to_merge = [ids for ids in people_ids_to_merge if len(ids) > 1]
        people_to_merge = [
            Person.objects.filter(id__in=group).order_by("name")
            for group in tqdm(people_ids_to_merge, unit="people")
        ]
        tqdm.write("-" * 80)

        if options["merge"]:
            self.merge_people(people_to_merge)

        if options["dry_run"]:
            print("Rolling back due to presence of '--dry-run'")
            transaction.set_rollback(True)

    def count_populated_fields(self, instance):
        return sum(
            [bool(field.value_to_string(instance)) for field in instance._meta.fields]
        )

    def get_primary_person(self, people_group):
        num_lowercase_characters_in_person_names = list(
            sum(1 for c in person.name if c.islower()) for person in people_group
        )

        # Prefer names with more lowercase letters (this is an attempt to keep things
        # standardized -- i.e. not have a bunch of all-caps names if we can avoid it)
        person_to_keep = people_group[
            num_lowercase_characters_in_person_names.index(
                max(num_lowercase_characters_in_person_names)
            )
        ]

        # TODO: Possible alternative method?
        # max_populated_fields = self.count_populated_fields(person_to_keep)
        # for person in people_group:
        #     populated_fields = self.count_populated_fields(person)
        #     if populated_fields > max_populated_fields:
        #         person_to_keep = person
        return person_to_keep

    @transaction.atomic
    def handle_merge_group(self, people_group):
        person_to_keep = self.get_primary_person(people_group)

        tqdm.write(
            f"Merging {people_group.count()} people named together under name "
            f"'{person_to_keep.name}'"
        )
        actually_different = set(person.name.lower() for person in people_group)
        if len(actually_different) > 1:
            tqdm.write("Names of other people being merged:")
            for name in actually_different:
                tqdm.write(f"  * {name}")

        merge_people(person_to_keep, list(people_group.exclude(id=person_to_keep.id)))
        tqdm.write("Saved the following non-empty alias field values:")
        tqdm.write(pformat(person_to_keep.merge_info.alias_field_values_summary))
        tqdm.write("Alias field values:")
        tqdm.write(pformat(person_to_keep.merge_info.alias_field_values))

    def merge_people(self, people_to_merge):
        for people_group in tqdm(people_to_merge, unit="groups"):
            self.handle_merge_group(people_group)
            tqdm.write("-" * 80)

    def build_merge_groups(self, threshold=THRESHOLD_DEFAULT, limit=None):
        people = Person.objects.all()
        if limit is not None:
            num_people = people.count() * limit
            people = Person.objects.filter(id__lt=num_people)
        tqdm.write(f"Processing {len(people)}/{Person.objects.count()} people")

        # A list of lists of the IDs of Person objects that need to be merged together
        people_ids_to_merge = []
        processed = set()
        for person in tqdm(people, unit="people"):
            unprocessed_people = people.exclude(id__in=processed)
            similar_people = find_similar_people(
                person, threshold=threshold, people=unprocessed_people
            )
            # We must exclude any people that have already been processed, because
            # this means they are already in people_ids_to_merge. If we didn't
            # exclude them here, we would get duplicates in people_ids_to_merge
            num_similar_people = similar_people.count()
            if num_similar_people > 1:
                tqdm.write(
                    f"Found {num_similar_people} names >{threshold} similar to "
                    f"name {person.name!r} and email {person.email!r}"
                )
                ids = list(similar_people.values_list("id", flat=True))
                people_ids_to_merge.append(ids)
                processed.update(ids)

        # "Inflate" the merge groups and count how many people are in each,
        # to get a total number of people that are going to merged
        total_people_to_merge = sum(
            len(person_group)
            for person_group in people_ids_to_merge
            if len(person_group) > 1
        )
        num_groups_to_merge = len(people_ids_to_merge)
        tqdm.write(
            f"Found {total_people_to_merge} total Person instances "
            f"that can be merged into {num_groups_to_merge} unique people"
        )

        return people_ids_to_merge

    def dump(self, people_ids_to_merge, path, **kwargs):
        with open(path, "w") as file:
            json.dump(list(people_ids_to_merge), file, **kwargs)

    def load(self, path, **kwargs):
        with open(path) as file:
            people_ids_to_merge = json.load(file, **kwargs)
            return people_ids_to_merge

    def compare_thresholds(self, thresholds):
        tqdm.write(f"Thresholds: {thresholds}")
        for threshold in thresholds:
            groups = self.build_merge_groups(threshold=threshold)
            self.dump(groups, f"people_t={threshold}.json")
