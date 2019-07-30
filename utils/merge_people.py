
from django.db.models import Q
from django.contrib.postgres.search import TrigramSimilarity

from django_super_deduper.merge import MergedModelInstance
from django_super_deduper.models import MergeInfo

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
    "data_source",
)


def find_similar_people(person, threshold=THRESHOLD_DEFAULT, people=None):
    if people is None:
        people = Person.objects.all()

    similar_people = (
        people
        # Annotate each item with its similarity ranking with the current name
        .annotate(
            name_similarity=TrigramSimilarity("name", person.name),
            email_similarity=TrigramSimilarity("email", person.email),
        )
        # And filter out anything below the given threshold
        .filter(
            # Names must be above similarity threshold
            Q(name_similarity__gt=threshold)
            # Emails must be either above the similarity threshold,
            # OR null. We don't want to exclude matches simply because they're
            # missing an email -- these are actually _easier_ to merge!
            & (Q(email_similarity__gt=threshold) | Q(email=""))
        ).exclude(id=person.id)
    )
    return similar_people


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

    # Avoid breaking serialization by replacing MIA instances with their ID
    for item in alias_field_values:
        if "model_import_attempt" in item:
            item["model_import_attempt"] = item["model_import_attempt"].id

    # Filter out fields that we have not whitelisted
    alias_field_values_summary = {
        k: v
        for k, v in alias_field_values_summary.items()
        if k in CONCRETE_PERSON_FIELDS
    }

    if alias_field_values_summary or alias_field_values:
        person.merge_info = MergeInfo.objects.create(
            alias_field_values_summary=alias_field_values_summary,
            alias_field_values=alias_field_values,
            # TODO: Do we really want to include the original?
            num_instances_merged=len(people_to_merge) + 1,
        )
        person.save()
    return person_to_keep
