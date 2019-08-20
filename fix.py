from django.utils.timezone import datetime, make_aware
from tqdm import tqdm
from pprint import pprint
from django.db import transaction
from django.core import serializers
from cases.models import Case, Person
from django.forms.models import model_to_dict
import json

OUTPUT_PATH = (
    "/home/nrqz.gb.nrao.edu/active/nrqz_admin/recently_modified_cases_fixture.json"
)


def do_serialize(
    since=make_aware(datetime(2019, 8, 15, 21)),
    recently_modified_cases=None,
    output_path=OUTPUT_PATH,
):
    if recently_modified_cases is None:
        recently_modified_cases = Case.objects.filter(modified_on__gt=since).order_by(
            "modified_on"
        )

    print(
        f"The following {recently_modified_cases.count()} cases have been modified since {since}:"
    )
    for case_num, mod_on in recently_modified_cases.values_list(
        "case_num", "modified_on"
    ):
        print(f"  {case_num}: {mod_on}")

    print(f"Dumping to {output_path}")
    recently_modified_cases_json = serializers.serialize(
        "json",
        recently_modified_cases,
        use_natural_foreign_keys=True,
        use_natural_primary_keys=True,
    )

    with open(output_path, "w") as file:
        file.write(recently_modified_cases_json)

    print("Success")


### deserialize


from pprint import pprint

from datadiff import diff

# from dictdiffer import diff

CONCRETE_FIELDS = [
    "is_active",
    "original_created_on",
    "original_modified_on",
    "data_source",
    "comments",
    "completed",
    "completed_on",
    "is_federal",
    "num_freqs",
    "num_sites",
    "radio_service",
    "date_recorded",
    "slug",
    "case_num",
    "shutdown",
    "sgrs_notify",
    "sgrs_responded_on",
    "call_sign",
    "freq_coord",
    "fcc_file_num",
    "num_outside",
    "original_meets_erpd_limit",
    "si_waived",
    "si",
    "original_si_done",
    "sgrs_service_num",
    "agency_num",
]

RELATION_FIELDS = ["applicant", "contact"]


def model_to_dict_with_filter(model, fields):
    model_as_dict = model_to_dict(model)
    model_as_dict = {
        key: value for key, value in model_as_dict.items() if key in fields
    }
    return model_as_dict


def deserialize_cases(path):
    with open(path) as file:
        # Deserialize Cases from file. This creates a generator of DeserializedModels
        deserialized_cases = serializers.deserialize(
            "json", file.read(), handle_forward_references=False
        )

    return deserialized_cases


def handle_new_case(deserialized_case):
    print(
        f"No existing case found with case number {deserialized_case.case_num}; creating a new one"
    )
    new_case = Case.objects.create(
        **model_to_dict_with_filter(deserialized_case, CONCRETE_FIELDS)
    )
    if deserialized_case.applicant:
        potential_applicants = Person.objects.filter(
            name=deserialized_case.applicant.name
        )
        if potential_applicants:
            new_case.applicant = potential_applicants.first()
    if deserialized_case.contact:
        potential_contacts = Person.objects.filter(name=deserialized_case.contact.name)
        if potential_contacts:
            new_case.contact = potential_contacts.first()
    new_case.save()
    # Print out the model values, including both (whitelisted) concrete and relation fields
    pprint(model_to_dict_with_filter(new_case, CONCRETE_FIELDS + RELATION_FIELDS))
    return new_case


def case_to_dict(case, relations=False):
    if relations:
        fields = CONCRETE_FIELDS + RELATION_FIELDS
    else:
        fields = CONCRETE_FIELDS
    case_as_dict = model_to_dict_with_filter(case, fields)

    # Purely for diff clarity, change the applicant/contact values from
    # their PK to their natural key (so that we can compare
    # names/emails to names/emails)
    case_as_dict.update(
        applicant=case.applicant.natural_key() if case.applicant else None,
        contact=case.contact.natural_key() if case.contact else None,
    )
    return case_as_dict


def handle_update_case(existing_case, deserialized_case):
    assert existing_case.case_num == deserialized_case.case_num
    Case.objects.filter(case_num=deserialized_case.case_num).update(
        **model_to_dict_with_filter(deserialized_case, CONCRETE_FIELDS)
    )
    existing_case.refresh_from_db()
    updated_case = existing_case
    if deserialized_case.applicant:
        potential_applicants = Person.objects.filter(
            name=deserialized_case.applicant.name
        )
        if potential_applicants:
            updated_case.applicant = potential_applicants.first()
    if deserialized_case.contact:
        potential_contacts = Person.objects.filter(name=deserialized_case.contact.name)
        if potential_contacts:
            updated_case.contact = potential_contacts.first()

    updated_case.save()

    return updated_case


def case_report(old_case_as_dict, new_case_as_dict):
    if old_case_as_dict:
        assert old_case_as_dict["case_num"] == new_case_as_dict["case_num"]
        print(f"Case {old_case_as_dict['case_num']} updated!")
        the_diff = diff(old_case_as_dict, new_case_as_dict)
        the_diff.diffs = [
            sdiff for sdiff in the_diff.diffs if sdiff[0] in ["delete", "insert"]
        ]
        if old_case_as_dict != new_case_as_dict:
            print("Changes: ", the_diff.stringify(include_preamble=False))
        else:
            print("No Changes")
    else:
        print(f"Case {new_case_as_dict['case_num']} created!")


def serializer_report(
    deserialized_cases,
    old_db_json_path="./sb_cases_fixture.json",
    new_db_json_path=OUTPUT_PATH,
):
    case_nums = [obj.object.case_num for obj in deserialized_cases]
    do_serialize(
        recently_modified_cases=Case.objects.filter(case_num__in=case_nums),
        output_path=old_db_json_path,
    )
    with open(old_db_json_path) as file:
        old_db_json = json.load(file)

    with open(new_db_json_path) as file:
        new_db_json = json.load(file)

    the_diff = diff(old_db_json, new_db_json)
    # the_diff.diffs = [
    #     sdiff for sdiff in the_diff.diffs if sdiff[0] in ["delete", "insert"]
    # ]
    print(the_diff.stringify(include_preamble=False))


@transaction.atomic
def do_deserialize(dry_run=True):
    deserialized_cases = list(deserialize_cases(OUTPUT_PATH))

    # Iterate through all of these Cases
    for deserialized_deserialized_case in deserialized_cases:
        # Pull out the actual Case object (not yet committed to the DB)
        deserialized_case = deserialized_deserialized_case.object

        print(f"Processing case {deserialized_case.case_num}")
        try:
            existing_case = Case.objects.get(case_num=deserialized_case.case_num)
        except Case.DoesNotExist:
            new_case = handle_new_case(deserialized_case)
            old_case_as_dict = None
        else:
            # Save a dictified version of the existing/current case
            old_case_as_dict = case_to_dict(existing_case)
            # Then update it with the information in the deserialized_case
            new_case = handle_update_case(existing_case, deserialized_case)

        new_case_as_dict = case_to_dict(new_case)
        case_report(old_case_as_dict, new_case_as_dict)
        print("---")

    # serializer_report(deserialized_cases)
    transaction.set_rollback(dry_run)
