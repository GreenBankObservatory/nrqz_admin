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

    def handle_record(self, row_data, durable=True):
        applicant, applicant_audit = APPLICANT_FORM_MAP.save_with_audit(
            row_data, imported_by=self.__module__
        )
        contact, contact_audit = CONTACT_FORM_MAP.save_with_audit(
            row_data, imported_by=self.__module__
        )
        pcase, pcase_audit = handle_case(
            row_data,
            form_map=PCASE_FORM_MAP,
            applicant=applicant,
            contact=contact,
            imported_by=self.__module__,
        )
        if pcase:
            attachments = handle_attachments(
                row_data, pcase, ATTACHMENT_FORM_MAPS, imported_by=self.__module__
            )
