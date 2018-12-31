"""Import Access Preliminary Application Data"""

from importers.handlers import handle_case, handle_attachments
from importers.access_prelim_application.fieldmap import (
    APPLICANT_FORM_MAP,
    CONTACT_FORM_MAP,
    PCASE_FORM_MAP,
    ATTACHMENT_FORM_MAPS,
)

from ._base_import import BaseImportCommand


class Command(BaseImportCommand):
    help = "Import Access Preliminary Application Data"

    def handle_row(self, row):
        applicant = APPLICANT_FORM_MAP.save(row)
        contact = CONTACT_FORM_MAP.save(row)
        pcase, pcase_created = handle_case(
            row, PCASE_FORM_MAP, applicant=applicant, contact=contact
        )
        attachments = handle_attachments(row, pcase, ATTACHMENT_FORM_MAPS)
