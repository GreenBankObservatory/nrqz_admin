import copy
import logging

from tabulate import tabulate

from django.db import connection
from django.db import transaction
from django.db.models import Model
from django.db.models.query import QuerySet
from django.test import TestCase

from utils.prompt import prompt

logger = logging.getLogger(__name__)
# print(logger)
# logger.setLevel(logging.DEBUG)

# ch = logging.StreamHandler()
# ch.setLevel(logging.DEBUG)

# logger.addHandler(ch)

# logger.debug("TEST")


def get_diffs(object_to_keep, objects_to_merge, field_whitelist=None):

    if field_whitelist:
        all_fields = field_whitelist
    else:
        all_fields = object_to_keep._meta.get_fields()

    # Modified from: https://djangosnippets.org/snippets/2283/
    for object_to_merge in objects_to_merge:
        local_fields = []
        singular_related_fields = []
        plural_related_fields = []
        for field in all_fields:
            if field.one_to_many or field.many_to_many:
                plural_related_fields.append(field)
            elif field.one_to_one:
                singular_related_fields.append(field)
            elif not field.is_relation:
                local_fields.append(field)
            else:
                raise ValueError(
                    "If this happens, run -- I have clearly "
                    "made an invalid assumption above"
                )

        logger.info("local_fields: %s", local_fields)
        logger.info("plural_related_fields: %s", plural_related_fields)
        logger.info("singular_related_fields: %s", singular_related_fields)

        local_objects_by_field = {}
        for field in local_fields:
            try:
                attribute_name = field.get_accessor_name()
            except AttributeError:
                attribute_name = field.get_attname()
            logger.debug("attribute_name: %s", attribute_name)
            value_in_object_to_keep = getattr(object_to_keep, attribute_name)
            value_in_object_to_merge = getattr(object_to_merge, attribute_name)

            logger.debug("value_in_object_to_keep: %s", value_in_object_to_keep)
            logger.debug("value_in_object_to_merge: %s", value_in_object_to_merge)
            if value_in_object_to_keep != value_in_object_to_merge:
                logger.debug("diff")
                if attribute_name not in local_objects_by_field:
                    local_objects_by_field[attribute_name] = set()

                logger.debug("added: %s", attribute_name)

                local_objects_by_field[attribute_name].add(value_in_object_to_merge)
            else:
                logger.debug("same")

        singular_related_objects_by_field = {}
        for field in singular_related_fields:
            try:
                attribute_name = field.get_accessor_name()
            except AttributeError:
                attribute_name = field.get_attname()
            logger.debug("attribute_name: %s", attribute_name)
            value_in_object_to_keep = getattr(object_to_keep, attribute_name)
            value_in_object_to_merge = getattr(object_to_merge, attribute_name)

            logger.debug("value_in_object_to_keep: %s", value_in_object_to_keep)
            logger.debug("value_in_object_to_merge: %s", value_in_object_to_merge)
            if value_in_object_to_keep != value_in_object_to_merge:
                logger.debug("diff")
                if attribute_name not in local_objects_by_field:
                    local_objects_by_field[attribute_name] = set()

                logger.debug("added: %s", attribute_name)

                local_objects_by_field[attribute_name].add(value_in_object_to_merge)
            else:
                logger.debug("same")

        plural_related_objects_by_field = {}
        for field in plural_related_fields:
            try:
                attribute_name = field.get_accessor_name()
            except AttributeError:
                attribute_name = field.get_attname()
            logger.debug("attribute_name: %s", attribute_name)

            objects_related_to_object_to_keep = getattr(
                object_to_keep, attribute_name
            ).all()
            objects_related_to_object_to_merge = getattr(
                object_to_merge, attribute_name
            ).all()
            logger.debug(
                "objects_related_to_object_to_keep: %s",
                objects_related_to_object_to_keep,
            )
            logger.debug(
                "objects_related_to_object_to_merge: %s",
                objects_related_to_object_to_merge,
            )
            plural_related_objects_by_field[attribute_name] = set(
                getattr(object_to_merge, attribute_name).all()
            )

        return {
            "local_objects": local_objects_by_field,
            "plural_related_objects": plural_related_objects_by_field,
            "singular_related_objects": singular_related_objects_by_field,
        }


def handle_local_field_diffs(model_object_to_keep, local_diffs, populate_blank=True):
    for field, possible_values in local_diffs.items():
        logger.debug("Processing {}: {}".format(field, possible_values))
        original_value = getattr(model_object_to_keep, field)
        if (
            populate_blank
            and original_value
            and not any(possible_values)
        ):
            val_to_set = possible_values.pop()
            logger.info("Setting previously-blank '%s' to '%s'", field, val_to_set)
        else:
            values = [original_value] + list(possible_values)
            choices = ["{}: '{}'".format(i, item) for i, item in enumerate(values)]
            choices_str = ", ".join(choices)
            response = prompt(
                "Cannot unambiguously derive a value for '{}'. "
                "Please select the value that you would "
                "like to set: {}".format(field, choices),
                range(len(choices)),
            )

            val_to_set = values[response]

            if response == 0:
                logger.info("Keeping original '%s': '%s'", field, original_value)
            else:
                logger.info(
                    "Changed '%s' from '%s' to '%s'", field, original_value, val_to_set
                )

        setattr(model_object_to_keep, field, val_to_set)

    model_object_to_keep.save()


def handle_plural_related_field_diffs(model_object_to_keep, related_diffs):
    for key, value in related_diffs.items():
        attribute_in_model_object_to_keep = getattr(model_object_to_keep, key)
        logger.debug(
            "Original model_object_to_keep's '%s': %s",
            key,
            attribute_in_model_object_to_keep,
        )
        logger.debug("New values of '%s': %s", key, value)
        attribute_in_model_object_to_keep.add(*value)
        logger.debug(
            "Updated model_object_to_keep's '%s': %s",
            key,
            getattr(model_object_to_keep, key),
        )


def handle_singular_related_field_diffs(model_object_to_keep, related_diffs):
    if related_diffs:
        raise NotImplementedError("Haven't had to handle this case yet")


# If the full merge is not successful, this will roll everything back
@transaction.atomic
def do_merge(
    model_object_to_keep,
    local_diffs,
    singular_related_diffs,
    plural_related_diffs,
    populate_blank=True,
):
    handle_local_field_diffs(model_object_to_keep, local_diffs, populate_blank)
    handle_singular_related_field_diffs(model_object_to_keep, singular_related_diffs)
    handle_plural_related_field_diffs(model_object_to_keep, plural_related_diffs)


def merge_model_objects(
    model_object_to_keep,
    model_objects_to_merge,
    field_whitelist=None,
    force=False,
    populate_blank=True,
):
    diffs = get_diffs(model_object_to_keep, model_objects_to_merge, field_whitelist)

    # logger.info("Local Objects:")
    # log_report(model_object_to_keep, diffs['local_objects'])
    # logger.info("One-to-One Related Objects:")
    # log_report(model_object_to_keep, diffs['singular_related_objects'])
    # logger.info("*-to-Many Related Objects:")
    # log_report(model_object_to_keep, diffs['plural_related_objects'])

    do_merge(
        model_object_to_keep,
        diffs["local_objects"],
        diffs["singular_related_objects"],
        diffs["plural_related_objects"],
        populate_blank,
    )

    all_diffs = {
        **diffs["local_objects"],
        **diffs["singular_related_objects"],
        **diffs["plural_related_objects"],
    }

    print("These are the final values of the relevant model fields:")
    print_summary(all_diffs, model_object_to_keep)
    for model in model_objects_to_merge:
        model.delete()


def log_report(model_object_to_keep, updated_fields):

    table = [[], [], []]
    for key, new_values in sorted(updated_fields.items()):
        old_value = getattr(model_object_to_keep, key)
        table[0].append(key)

        if hasattr(old_value, "all"):
            old_value_pretty = "\n".join([str(val) for val in old_value.all()])
        else:
            old_value_pretty = str(old_value)
        table[1].append(old_value_pretty)

        new_values_pretty = []
        for value in new_values:
            if hasattr(value, "all"):
                new_values_pretty.append("\n".join([str(val) for val in value.all()]))
            else:
                new_values_pretty.append(str(value))

        table[2].append("\n".join(new_values_pretty))

    logger.info(
        tabulate(
            zip(*table),
            headers=["Attribute", "Old Value", "Possible Values"],
            tablefmt="grid",
        )
    )


def print_summary(diffs, updated_model_object, fields=None, show_unchanged=True):
    table = []

    if not fields:
        fields = diffs.keys()

    for field in fields:

        old_value = diffs[field]
        if not isinstance(old_value, set):
            raise ValueError("All diff fields must be set() instances!")

        new_value = getattr(updated_model_object, field)

        old_value_pretty_list = []
        try:
            old_value_as_list = sorted(old_value, key=lambda x: x.id)
        except AttributeError:
            old_value_as_list = sorted(old_value)

        for value in old_value_as_list:
            if hasattr(value, "id"):
                old_value_pretty_list.append("{}: {}".format(value.id, str(value)))
            else:
                old_value_pretty_list.append(str(value))

        old_value_pretty = "\n".join(old_value_pretty_list)

        if hasattr(new_value, "all"):
            new_value_as_set = set(new_value.all())
        else:
            new_value_as_set = set([new_value])

        new_value_pretty_list = []
        try:
            new_value_as_list = sorted(new_value_as_set, key=lambda x: x.id)
        except AttributeError:
            new_value_as_list = sorted(new_value_as_set)

        for value in new_value_as_list:
            if hasattr(value, "id"):
                new_value_pretty_list.append("{}: {}".format(value.id, str(value)))
            else:
                new_value_pretty_list.append(str(value))

        new_value_pretty = "\n".join(new_value_pretty_list)

        changed = "No" if new_value_as_set == old_value else "Yes"
        if changed or show_unchanged:
            table.append([field, old_value_pretty, new_value_pretty, changed])

    print(
        tabulate(
            table,
            headers=["Field", "Original Value", "New Value", "Changed"],
            tablefmt="grid",
        )
    )
