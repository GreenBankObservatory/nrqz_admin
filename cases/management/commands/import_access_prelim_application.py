"""Import Access Preliminary Application Data"""

import re

from tqdm import tqdm

from django.db.models import Q

from django_import_data import BaseImportCommand
from django_import_data.models import RowData

from importers.handlers import handle_case, handle_attachments
from importers.access_prelim_application.formmaps import (
    APPLICANT_FORM_MAP,
    CONTACT_FORM_MAP,
    PCASE_FORM_MAP,
    ATTACHMENT_FORM_MAPS,
    IGNORED_HEADERS,
)


from cases.models import Case, PreliminaryCase, CaseGroup
from utils.constants import ACCESS_PRELIM_APPLICATION

# https://regex101.com/r/g6NM6e/1
CASE_REGEX = re.compile(
    r"(?:(?:NRQZ ID )|(?:NRQZ#)|(?:Case\s*))(?P<case_num>\d+)", re.IGNORECASE
)
PCASE_REGEX = re.compile(r"NRQZ#P(\d+)", re.IGNORECASE)


def derive_case_num(pcase):
    """Given a pcase, attempt to derive a case number that it is related to"""

    m = CASE_REGEX.search(pcase.comments)
    if m:
        case_num = int(m.groupdict()["case_num"])
    else:
        case_num = None

    return case_num


def derive_related_pcase_nums(pcase):
    """Given a pcase, attempt to derive all related pcase numbers"""

    m = PCASE_REGEX.findall(pcase.comments)
    if m:
        pcase_nums = [int(pcase_num) for pcase_num in m]
    else:
        pcase_nums = []

    return pcase_nums


def handle_pcase_group(pcase):
    """Add the given PCase, and related PCases, to a PCaseGroup"""
    # Determine whether there are any related PCases (i.e. other PCase numbers
    # mentioned in the comments)
    related_pcase_nums = derive_related_pcase_nums(pcase)
    if related_pcase_nums:
        related_pcases = PreliminaryCase.objects.filter(
            Q(case_num__in=[pcase.case_num, *related_pcase_nums])
            | Q(case__prelim_cases__case_num__in=[pcase.case_num, *related_pcase_nums])
        ).distinct()
        tqdm.write(f"rpc: {related_pcases}")
        # Now, grab the unique set of all existing, PCaseGroups that these related
        # PCases are already associated with
        existing_case_group_ids = related_pcases.filter(
            case_groups__isnull=False
        ).values("case_groups")

        existing_case_groups = CaseGroup.objects.filter(id__in=existing_case_group_ids)
        # If there aren't any, then we'll need to create one
        if existing_case_groups.count() == 0:
            case_group = CaseGroup.objects.create()
            tqdm.write(f"Created {case_group}")
        # If there is exactly one already in existence, we can just use it
        elif existing_case_groups.count() == 1:
            case_group = existing_case_groups.first()
            tqdm.write(f"Found {case_group}")
        # If there is more than one, then we need to merge them together
        else:
            # Pick the first one as the one to keep (doesn't actually matter which one)
            pcase_group_to_keep = existing_case_groups.first()
            # We need to generate a list in memory from the QuerySet so that
            # this will be accurate after the deletions
            existing_case_groups_ids = list(
                existing_case_groups.values_list("id", flat=True)
            )
            # Update all of the related PCase's PCGs to the one we want to keep
            # Delete the others, since they serve no purpose now
            existing_case_groups.exclude(id=pcase_group_to_keep.id).delete()
            tqdm.write(
                f"Found multiple existing PCGs {existing_case_groups_ids}. "
                f"Set all PCGs to {pcase_group_to_keep}, kept "
                f"{pcase_group_to_keep.id}, and deleted the others"
            )
            case_group = pcase_group_to_keep

        case_group.pcases.add(*related_pcases)

        return related_pcases, case_group
    return None, None


def post_import_actions():
    tqdm.write("Deriving PCaseGroups")
    progress = tqdm(PreliminaryCase.objects.all(), unit="PCase")
    for pcase in progress:
        progress.desc = f"Processing {pcase}"
        derive_cases_from_comments(pcase)
        handle_pcase_group(pcase)

    tqdm.write("Linking Cases to PreliminaryCases")
    for case in tqdm(Case.objects.all(), unit="Case"):
        progress.desc = f"Processing {case}"
        related_pcases, case_group = handle_pcase_group(case)
        if related_pcases:
            related_pcases.update(case=case)
        if case_group:
            case_group.cases.add(case)


# Future Thomas:
# We are most of the way to transitioning to the new CaseGroup concept, which
# bundles cases and pcases together with MtM fields
# Still need to update all of the filters/tables/views, and expand the unit tests.
# PC importer is testing clean, but C importer is almost certainly hosed
# Still need to expand sanity checks, too, and expand regexes to capture _all_ case mentions, not just the first


def derive_cases_from_comments(pcase):
    case_num = derive_case_num(pcase)
    if case_num:
        tqdm.write(f"Found case ID {case_num} in PCase {pcase} comments")
        if pcase.case and pcase.case.case_num != case_num:
            raise ValueError(
                f"PCase {pcase} already has a case number ({pcase.case}) "
                f"and it's different than the derived case number: {case_num}"
            )
        try:
            pcase.case = Case.objects.get(case_num=case_num)
            pcase.save()
        except Case.DoesNotExist:
            tqdm.write(
                f"Found case ID {case_num} in PCase {pcase} comments, but no matching Case found"
            )
            tqdm.write(pcase.comments)
            tqdm.write("\n")
            tqdm.write("-" * 80)
        # else:
        #     tqdm.write(
        #         f"Successfully derived case {pcase.case} from {pcase} comments"
        #     )


class Command(BaseImportCommand):
    help = "Import Access Preliminary Application Data"

    PROGRESS_TYPE = BaseImportCommand.PROGRESS_TYPES.ROW
    # TODO: This is somewhat stupid; think of a better way
    FORM_MAPS = [
        APPLICANT_FORM_MAP,
        CONTACT_FORM_MAP,
        PCASE_FORM_MAP,
        *ATTACHMENT_FORM_MAPS,
    ]
    IGNORED_HEADERS = IGNORED_HEADERS

    def post_import_actions(self):
        post_import_actions()

    def handle_record(self, row_data, file_import_attempt, durable=True):
        applicant, applicant_audit = APPLICANT_FORM_MAP.save_with_audit(
            row_data,
            file_import_attempt=file_import_attempt,
            imported_by=self.__module__,
        )
        contact, contact_audit = CONTACT_FORM_MAP.save_with_audit(
            row_data,
            file_import_attempt=file_import_attempt,
            imported_by=self.__module__,
        )
        pcase, pcase_audit = handle_case(
            row_data,
            form_map=PCASE_FORM_MAP,
            applicant=applicant,
            contact=contact,
            file_import_attempt=file_import_attempt,
            imported_by=self.__module__,
        )
        if pcase:
            attachments = handle_attachments(
                row_data,
                pcase,
                ATTACHMENT_FORM_MAPS,
                file_import_attempt=file_import_attempt,
                imported_by=self.__module__,
            )
