from importers.handlers import handle_case, handle_attachments
from importers.access_application.fieldmap import (
    APPLICANT_FORM_MAP,
    CONTACT_FORM_MAP,
    CASE_FORM_MAP,
    ATTACHMENT_FORM_MAPS,
)
from django_import_data import BaseImportCommand
from django_import_data.models import RowData


class Command(BaseImportCommand):
    help = "Import Access Application Data"

    def handle_row(self, row, batch_import):
        row_data = RowData.objects.create(data=row)
        applicant, applicant_audit = APPLICANT_FORM_MAP.save_with_audit(
            row_data=row_data, batch_import=batch_import
        )
        contact, contact_audit = CONTACT_FORM_MAP.save_with_audit(
            row_data=row_data, batch_import=batch_import
        )
        case, case_audit = handle_case(
            row_data,
            CASE_FORM_MAP,
            applicant=applicant.id if applicant else None,
            contact=contact.id if contact else None,
            batch_import=batch_import,
        )
        attachments = handle_attachments(
            row, case, ATTACHMENT_FORM_MAPS, batch_import=batch_import
        )

        audits = {
            "applicant": applicant_audit,
            "contact": contact_audit,
            "pcase": case_audit,
        }
        return audits
