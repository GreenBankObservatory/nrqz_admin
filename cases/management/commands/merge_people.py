"""Merge People together!"""

from pprint import pformat
from collections import Counter
import json

from tqdm import tqdm

from django.db import transaction
from django.contrib.postgres.search import TrigramSimilarity

from django_import_data import BaseImportCommand
from django_super_deduper.merge import MergedModelInstance

from cases.models import Person

THRESHOLD_DEFAULT = 0.9

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


def proportion(value):
    value = float(value)
    if not 0 < value <= 1:
        raise ValueError("Value out of range")
    return value


class Command(BaseImportCommand):

    help = "Merge Person objects together"

    def add_arguments(self, parser):
        parser.add_argument(
            "-i",
            "--input",
            help="The path to an input JSON file, as created by --output",
        )
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "-o",
            "--output",
            help="The path to an output JSON file. This is a list of model groups, "
            "where each model group is a list of IDs. e.g. [[1,2,3],[4,5,6]].",
        )
        group.add_argument(
            "-t",
            "--threshold",
            type=proportion,
            default=THRESHOLD_DEFAULT,
            help="The threshold for which names are considered a match (based "
            "on trigram similarity). Value of '1' means exact matches only",
        )
        group.add_argument("--merge", action="store_true", help="Merge people")

        parser.add_argument(
            "-l",
            "--limit",
            type=proportion,
            help="Specify a random percentage [0.0 - 1.0] of rows that should be processed",
        )
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["input"]:
            people_ids_to_merge = self.load(options["input"])
        elif options["threshold"]:
            people_ids_to_merge = self.find_similar_people(
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

        max_populated_fields = self.count_populated_fields(person_to_keep)
        for person in people_group:
            populated_fields = self.count_populated_fields(person)
            if populated_fields > max_populated_fields:
                person_to_keep = person

        (
            person,
            alias_field_values_summary,
            alias_field_values,
        ) = MergedModelInstance.create_with_change_tracking(
            person_to_keep,
            list(people_group.exclude(id=person_to_keep.id)),
            keep_old=False,
        )
        person.alias_field_values_summary = {
            k: v
            for k, v in alias_field_values_summary.items()
            if k in CONCRETE_PERSON_FIELDS
        }
        for key in alias_field_values:
            key["model_import_attempt"] = key["model_import_attempt"].id
        person.alias_field_values = alias_field_values
        person.save()
        if person.alias_field_values_summary:
            tqdm.write("Saved the following non-empty alias field values:")
            tqdm.write(pformat(person.alias_field_values_summary))
        if person.alias_field_values:
            tqdm.write("Alias field values:")
            tqdm.write(pformat(person.alias_field_values))

        return []

    def merge_people(self, people_to_merge):
        for people_group in tqdm(people_to_merge, unit="groups"):
            self.handle_merge_group(people_group)
            tqdm.write("-" * 80)

    def find_similar_people(self, threshold=THRESHOLD_DEFAULT, limit=None):
        people = Person.objects.all()
        if limit is not None:
            num_people = people.count() * limit
            people = Person.objects.filter(id__lt=num_people)
        tqdm.write(f"Processing {len(people)}/{Person.objects.count()} people")

        # A list of lists of the IDs of Person objects that need to be merged together
        people_ids_to_merge = []
        processed = set()
        for name in tqdm(people.values_list("name", flat=True), unit="people"):
            similar_people = (
                # We must exclude any people that have already been processed, because
                # this means they are already in people_ids_to_merge. If we didn't
                # exclude them here, we would get duplicates in people_ids_to_merge
                people.exclude(id__in=processed)
            )
            # If threshold is less than 1, we do a similarity search
            if threshold < 1:
                similar_people = (
                    similar_people
                    # Annotate each item with its similarity ranking with the current name
                    .annotate(similarity=TrigramSimilarity("name__unaccent", name))
                    # And filter out anything below the given threshold
                    .filter(similarity__gt=threshold)
                )
            # If not, we don't want the overhead of similarity search
            else:
                similar_people = similar_people.filter(name__unaccent__iexact=name)
            num_similar_people = similar_people.count()
            if num_similar_people > 1:
                comparitor = "similar" if threshold < 1 else "identical"
                tqdm.write(f"Found {num_similar_people} names {comparitor} to {name!r}")
                # for similar_person in similar_people.all():
                #     tqdm.write(f"  {similar_person.name!r} (id: {similar_person.id})")

                ids = list(similar_people.values_list("id", flat=True))
                people_ids_to_merge.append(ids)
                processed.update(ids)

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
            groups = self.find_similar_people(threshold=threshold)
            self.dump(groups, f"people_t={threshold}.json")
