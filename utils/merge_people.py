from django.db import transaction
from django.db.models import Q
from django.contrib.postgres.search import TrigramSimilarity

from django_super_deduper.merge import MergedModelInstance
from django_super_deduper.models import MergeInfo

from cases.models import Person, Case, PreliminaryCase

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
    "data_source",
)

CONTACT_VALUES = ["contact"]
APPLICANT_VALUES = ["applicant"]


def _find_similar_people(name, email="", people=None, threshold=THRESHOLD_DEFAULT):
    if people is None:
        people = Person.objects.all()
    return (
        people
        # Annotate each item with its similarity ranking with the current name
        .annotate(
            name_similarity=TrigramSimilarity("name", name),
            email_similarity=TrigramSimilarity("email", email),
        )
        # And filter out anything below the given threshold
        .filter(
            # Names must be above similarity threshold
            Q(name_similarity__gt=threshold)
            # Emails must be either above the similarity threshold,
            # OR null. We don't want to exclude matches simply because they're
            # missing an email -- these are actually _easier_ to merge!
            & (Q(email_similarity__gt=threshold) | Q(email=""))
        )
    )


def find_similar_people(person, threshold=THRESHOLD_DEFAULT, people=None):
    similar_people = _find_similar_people(
        person.name, person.email, threshold=threshold, people=people
    ).exclude(id=person.id)
    return similar_people


@transaction.atomic
def _handle_cross_references(
    model_class, from_field, to_field, threshold=THRESHOLD_DEFAULT
):
    """"Expand" all references of from_field to to_field with proper FKs

    For example, if we have some PreliminaryCases where the `contact` field is set to a
    Person named "applicant", this will:
    * Set each of these cases' contact to the value of its applicant
    * Delete the old person... maybe????
    """
    cases = (
        model_class.objects.annotate(
            name_similarity=TrigramSimilarity(f"{from_field}__name", to_field)
        )
        # And filter out anything below the given threshold
        .filter(
            # Names must be above similarity threshold
            Q(name_similarity__gt=threshold)
        )
    )

    for case in cases.all():
        from_field_value = getattr(case, from_field)
        to_field_value = getattr(case, to_field)
        setattr(case, from_field, to_field_value)
        print(f"Set {case} '{from_field}' to '{to_field}': '{to_field_value!r}'")
        case.save()
        deletions = from_field_value.delete()
        if deletions[0] != 1:
            raise ValueError(
                f"Unexpected number of deletions encountered when attempting to delete {from_field_value!r}: {deletions}\n"
                "There should only be one deletion! Check logic in _handle_cross_references"
            )


@transaction.atomic
def handle_cross_references(threshold=THRESHOLD_DEFAULT):
    # Handle PreliminaryCases where the contact references the applicant
    _handle_cross_references(
        PreliminaryCase, "contact", "applicant", threshold=threshold
    )
    # Handle PreliminaryCases where the applicant references the contact
    _handle_cross_references(
        PreliminaryCase, "applicant", "contact", threshold=threshold
    )
    # Handle Cases where the contact references the applicant
    _handle_cross_references(Case, "applicant", "contact", threshold=threshold)
    # Handle Cases where the applicant references the contact
    _handle_cross_references(Case, "contact", "applicant", threshold=threshold)


def merge_people(person_to_keep, people_to_merge):
    (
        person,
        alias_field_values_summary,
        alias_field_values,
    ) = MergedModelInstance.create_with_change_tracking(
        person_to_keep,
        people_to_merge,
        # This deletes the merged instances
        keep_old=False,
    )

    existing_merge_infos = []
    # Avoid breaking serialization by replacing MIA instances with their ID
    for item in alias_field_values:
        if "model_import_attempt" in item:
            item["model_import_attempt"] = item["model_import_attempt"].id

        if "merge_info" in item:
            # Add to list, and remove from item itself (will be merged later)
            existing_merge_infos.append(item.pop("merge_info"))

    # Filter out fields that we have not whitelisted
    alias_field_values_summary = {
        k: v
        for k, v in alias_field_values_summary.items()
        if k in CONCRETE_PERSON_FIELDS
    }

    if alias_field_values_summary or alias_field_values:
        merge_info = MergeInfo.objects.create(
            alias_field_values_summary=alias_field_values_summary,
            alias_field_values=alias_field_values,
            num_instances_merged=len(people_to_merge) + 1,
        )
        # Merge together
        if existing_merge_infos:
            merge_info = MergedModelInstance.create(merge_info, existing_merge_infos)
            print("!!!", merge_info)

        person.merge_info = merge_info
        person.save()
    return person_to_keep
