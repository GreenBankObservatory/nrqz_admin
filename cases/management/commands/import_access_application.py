"""Import Access Application Data"""

import re

from tqdm import tqdm

from django.db import transaction

from django_import_data import BaseImportCommand
from django_import_data.models import RowData

from importers.handlers import handle_case, handle_attachments
from importers.access_application.formmaps import (
    APPLICANT_FORM_MAP,
    CONTACT_FORM_MAP,
    CASE_FORM_MAP,
    ATTACHMENT_FORM_MAPS,
    IGNORED_HEADERS,
)

from cases.models import Case, CaseGroup
from utils.constants import ACCESS_APPLICATION


CASE_REGEX = re.compile(
    r"(?:(?:NRQZ ID )|(?:NRQZ#)|(?:Case\s*))(?P<case_num>\d+)", re.IGNORECASE
)
CASE_REGEX2 = re.compile(r"(?P<case_num>\d{3,})-\d{,4}")


def derive_related_case_nums(case):
    matches1 = CASE_REGEX.findall(case.comments)
    matches2 = CASE_REGEX2.findall(case.comments)

    case_nums = set()
    if matches1:
        case_nums.update(int(case_num) for case_num in matches1)

    if matches2:
        case_nums.update(int(case_num) for case_num in matches2)

    return list(case_nums)


def handle_case_group(case):
    related_case_nums = derive_related_case_nums(case)
    if related_case_nums:
        # If there are, grab all of them
        related_cases = Case.objects.filter(
            case_num__in=[case.case_num, *related_case_nums]
        )
        # For diagnostic purposes, let us know if any of them cannot be found
        unique_requested_case_nums = set(related_case_nums)
        unique_related_case_nums = set(related_cases.values_list("case_num", flat=True))
        if unique_requested_case_nums != unique_related_case_nums:
            diff = unique_related_case_nums.difference(unique_requested_case_nums)
            tqdm.write(f"One or more Cases not found! Failed to find: {diff}")

        # Now, grab the unique set of all existing, CaseGroups that these related
        # Cases are already associated with
        existing_case_group_ids = (
            related_cases.filter(case_group__isnull=False)
            .order_by("case_group")
            .values("case_group")
            .distinct()
        )
        existing_case_groups = CaseGroup.objects.filter(id__in=existing_case_group_ids)
        # print(existing_case_groups)
        # If there aren't any, then we'll need to create one
        if existing_case_groups.count() == 0:
            case_group = CaseGroup.objects.create(data_source=ACCESS_APPLICATION)
            tqdm.write(f"Created {case_group}")
        # If there is exactly one already in existence, we can just use it
        elif existing_case_groups.count() == 1:
            case_group = CaseGroup.objects.get(id=existing_case_groups.first().id)
            tqdm.write(f"Found {case.case_group}")
        # If there is more than one, then we need to merge them together
        else:
            # Pick the first one as the one to keep (doesn't actually matter which one)
            case_group_to_keep = existing_case_groups.first()
            existing_case_groups_ids = list(
                existing_case_groups.values_list("id", flat=True)
            )
            # Delete the others, since they serve no purpose now
            existing_case_groups.exclude(id=case_group_to_keep.id).delete()
            tqdm.write(
                f"Found multiple existing PCGs {existing_case_groups_ids}. "
                f"Set all PCGs to {case_group_to_keep}, kept "
                f"{case_group_to_keep.id}, and deleted the others"
            )
            case_group = case_group_to_keep

        related_cases.update(case_group=case_group)


def post_import_actions():
    tqdm.write("Deriving CaseGroups")
    progress = tqdm(Case.objects.all(), unit="case")
    for case in progress:
        progress.desc = f"Processing {case}"
        handle_case_group(case)


class Command(BaseImportCommand):
    help = "Import Access Application Data"

    PROGRESS_TYPE = BaseImportCommand.PROGRESS_TYPES.ROW

    # TODO: This is somewhat stupid; think of a better way
    FORM_MAPS = [
        APPLICANT_FORM_MAP,
        CONTACT_FORM_MAP,
        CASE_FORM_MAP,
        *ATTACHMENT_FORM_MAPS,
    ]
    IGNORED_HEADERS = IGNORED_HEADERS

    def post_import_actions(self):
        post_import_actions()

    def handle_record(self, row_data, file_import_attempt, durable=True):
        applicant, applicant_audit = APPLICANT_FORM_MAP.save_with_audit(
            row_data=row_data,
            file_import_attempt=file_import_attempt,
            imported_by=self.__module__,
        )
        contact, contact_audit = CONTACT_FORM_MAP.save_with_audit(
            row_data=row_data,
            file_import_attempt=file_import_attempt,
            imported_by=self.__module__,
        )
        case, case_audit = handle_case(
            row_data,
            CASE_FORM_MAP,
            applicant=applicant,
            contact=contact,
            file_import_attempt=file_import_attempt,
            imported_by=self.__module__,
        )
        # TODO: If durable?? In the interest of catching _all_ errors...
        if case:
            attachments = handle_attachments(
                row_data,
                case,
                ATTACHMENT_FORM_MAPS,
                file_import_attempt=file_import_attempt,
                imported_by=self.__module__,
            )
