import csv

from importers.handlers import handle_case, handle_attachments
from importers.access_application.fieldmap import (
    APPLICANT_FORM_MAP,
    CONTACT_FORM_MAP,
    CASE_FORM_MAP,
    ATTACHMENT_FORM_MAPS,
)
from ._base_import import BaseImportCommand


class Command(BaseImportCommand):
    help = "Import Access Application Data"

    def handle_row(self, row):
        applicant = APPLICANT_FORM_MAP.save(row)
        contact = CONTACT_FORM_MAP.save(row)
        case, case_created = handle_case(
            row,
            CASE_FORM_MAP,
            applicant=applicant.id if applicant else None,
            contact=contact.id if contact else None,
        )
        attachments = handle_attachments(row, case, ATTACHMENT_FORM_MAPS)
