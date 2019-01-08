"""Import Access Preliminary Application Data"""

from importers.handlers import handle_case, handle_attachments
from importers.access_prelim_application.fieldmap import (
    APPLICANT_FORM_MAP,
    CONTACT_FORM_MAP,
    PCASE_FORM_MAP,
    ATTACHMENT_FORM_MAPS,
)

from django_import_data import BaseImportCommand
from django_import_data.models import RowAudit


class Command(BaseImportCommand):
    help = "Import Access Preliminary Application Data"

    def handle_row(self, row):
        row_audit = RowAudit.objects.create(data=row)
        applicant, applicant_audit = APPLICANT_FORM_MAP.save_with_audit(
            row, row_audit=row_audit
        )
        contact, contact_audit = CONTACT_FORM_MAP.save_with_audit(
            row, row_audit=row_audit
        )
        pcase, pcase_audit = handle_case(
            row,
            PCASE_FORM_MAP,
            applicant=applicant,
            contact=contact,
            row_audit=row_audit,
        )
        attachments = handle_attachments(row, pcase, ATTACHMENT_FORM_MAPS)
        audits = {
            "applicant": applicant_audit,
            "contact": contact_audit,
            "pcase": pcase_audit,
        }
        return audits
