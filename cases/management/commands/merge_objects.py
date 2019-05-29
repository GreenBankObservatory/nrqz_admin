# -*- coding: utf-8 -*-

from collections import Counter

from django.apps import apps
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.management import BaseCommand
from django.db import transaction
from django_extensions.management.utils import signalcommand

from tqdm import tqdm

from pprint import pformat

from cases.models import Person


def get_model_to_deduplicate():
    models = apps.get_models()
    iterator = 1
    for model in models:
        tqdm.write("%s. %s" % (iterator, model.__name__))
        iterator += 1
    model_choice = int(
        input(
            """
        Enter the number of the model you would like to de-duplicate:
        """
        )
    )
    model_to_deduplicate = models[model_choice - 1]
    return model_to_deduplicate


def get_field_names(model):
    fields = [field.name for field in model._meta.get_fields()]
    iterator = 1
    for field in fields:
        tqdm.write("%s. %s" % (iterator, field))
        iterator += 1
    validated = False
    while not validated:
        first_field = int(
            input(
                """
            Enter the number of the (first) field you would like to de-duplicate.
            """
            )
        )
        if first_field in range(1, iterator):
            validated = True
        else:
            tqdm.write("Invalid input. Please try again.")
    fields_to_deduplicate = [fields[first_field - 1]]

    done = False
    while not done:
        available_fields = [f for f in fields if f not in fields_to_deduplicate]
        iterator = 1
        for field in available_fields:
            tqdm.write("%s. %s" % (iterator, field))
            iterator += 1
        tqdm.write("C. Done adding fields.")

        validated = False
        while not validated:
            tqdm.write("You are currently deduplicating on the following fields:")
            tqdm.write("".join(fields_to_deduplicate) + "")

            additional_field = input(
                """
                Enter the number of the field you would like to de-duplicate.
                If you have entered all fields, enter C to continue.
                """
            )
            if additional_field == "C":
                done = True
                validated = True
            elif int(additional_field) in list(range(1, len(available_fields) + 1)):
                fields_to_deduplicate += [available_fields[int(additional_field) - 1]]
                validated = True
            else:
                tqdm.write("Invalid input. Please try again.")

    return fields_to_deduplicate


def keep_first_or_last_instance():
    while True:
        first_or_last = input(
            """
            Do you want to keep the first or last duplicate instance?
            Enter "first" or "last" to continue.
            """
        )
        if first_or_last in ["first", "last"]:
            return first_or_last


def get_generic_fields():
    """Return a list of all GenericForeignKeys in all models."""
    generic_fields = []
    for model in apps.get_models():
        for field_name, field in model.__dict__.items():
            if isinstance(field, GenericForeignKey):
                generic_fields.append(field)
    return generic_fields


class Command(BaseCommand):
    help = """
        Removes duplicate model instances based on a specified
        model and field name(s).

        Makes sure that any OneToOne, ForeignKey, or ManyToMany relationships
        attached to a deleted model(s) get reattached to the remaining model.

        Based on the following:
        https://djangosnippets.org/snippets/2283/
        https://stackoverflow.com/a/41291137/2532070
        https://gist.github.com/edelvalle/01886b6f79ba0c4dce66
        """

    @signalcommand
    def handle(self, *args, **options):
        # model = get_model_to_deduplicate()
        model_class = Person
        # field_names = get_field_names(model_class)
        field_names = ["name"]
        # first_or_last = keep_first_or_last_instance()
        first_or_last = "first"
        total_num_deletions = 0
        all_deletions = Counter()
        for instance in tqdm(model_class.objects.all(), unit="objects"):
            kwargs = {}
            for field_name in field_names:
                instance_field_value = instance.__getattribute__(field_name)
                kwargs.update({field_name: instance_field_value})
            try:
                model_class.objects.get(**kwargs)
            except model_class.MultipleObjectsReturned:
                instances = model_class.objects.filter(**kwargs)

                if first_or_last == "first":
                    primary_object = instances[0]
                    alias_objects = instances[1:]
                elif first_or_last == "last":
                    primary_object = instances[len(instances) - 1]
                    alias_objects = instances[: len(instances) - 1]
                primary_object, num_deletions, deletions = self.merge_model_instances(
                    primary_object, alias_objects
                )
                total_num_deletions += num_deletions
                all_deletions += deletions

        tqdm.write(f"Successfully deleted {total_num_deletions} model instances:")
        tqdm.write(pformat(all_deletions))

    @transaction.atomic()
    def merge_model_instances(self, primary_object, alias_objects):
        """Merge several model instances into one, the `primary_object`.
        Use this function to merge model objects and migrate all of the related
        fields from the alias objects the primary object.
        """
        generic_fields = get_generic_fields()

        # get related fields
        related_fields = list(
            filter(lambda x: x.is_relation is True, primary_object._meta.get_fields())
        )

        many_to_many_fields = list(
            filter(lambda x: x.many_to_many is True, related_fields)
        )

        related_fields = list(filter(lambda x: x.many_to_many is False, related_fields))

        # Loop through all alias objects and migrate their references to the
        # primary object
        total_num_deletions = 0
        all_deletions = Counter()
        for alias_object in alias_objects:
            # Migrate all foreign key references from alias object to primary
            # object.
            for many_to_many_field in many_to_many_fields:
                alias_varname = many_to_many_field.name
                related_objects = getattr(alias_object, alias_varname)
                for obj in related_objects.all():
                    try:
                        # Handle regular M2M relationships.
                        getattr(alias_object, alias_varname).remove(obj)
                        getattr(primary_object, alias_varname).add(obj)
                    except AttributeError:
                        # Handle M2M relationships with a 'through' model.
                        # This does not delete the 'through model.
                        # TODO: Allow the user to delete a duplicate 'through' model.
                        through_model = getattr(alias_object, alias_varname).through
                        kwargs = {
                            many_to_many_field.m2m_reverse_field_name(): obj,
                            many_to_many_field.m2m_field_name(): alias_object,
                        }
                        through_model_instances = through_model.objects.filter(**kwargs)
                        for instance in through_model_instances:
                            # Re-attach the through model to the primary_object
                            setattr(
                                instance,
                                many_to_many_field.m2m_field_name(),
                                primary_object,
                            )
                            instance.save()
                            # TODO: Here, try to delete duplicate instances that are
                            # disallowed by a unique_together constraint

            for related_field in related_fields:
                if related_field.one_to_many:
                    alias_varname = related_field.get_accessor_name()
                    related_objects = getattr(alias_object, alias_varname)
                    for obj in related_objects.all():
                        field_name = related_field.field.name
                        setattr(obj, field_name, primary_object)
                        obj.save()
                elif related_field.one_to_one or related_field.many_to_one:
                    alias_varname = related_field.name
                    related_object = getattr(alias_object, alias_varname)
                    primary_related_object = getattr(primary_object, alias_varname)
                    if primary_related_object is None:
                        setattr(primary_object, alias_varname, related_object)
                        primary_object.save()
                    elif related_field.one_to_one:
                        tqdm.write(
                            "Deleted {} with id {}".format(
                                related_object, related_object.id
                            )
                        )
                        num_deletions, deletions = related_object.delete()
                        total_num_deletions += num_deletions
                        all_deletions += deletions

            for field in generic_fields:
                filter_kwargs = {}
                filter_kwargs[field.fk_field] = alias_object._get_pk_val()
                filter_kwargs[field.ct_field] = field.get_content_type(alias_object)
                related_objects = field.model.objects.filter(**filter_kwargs)
                for generic_related_object in related_objects:
                    setattr(generic_related_object, field.name, primary_object)
                    generic_related_object.save()

            if alias_object.id:
                num_deletions, deletions = alias_object.delete()
                tqdm.write(
                    "Somehow alias object hasn't been deleted yet; deleted {} with id {}".format(
                        alias_object, alias_object.id
                    )
                )
                total_num_deletions += num_deletions
                all_deletions += deletions

        return primary_object, total_num_deletions, all_deletions
