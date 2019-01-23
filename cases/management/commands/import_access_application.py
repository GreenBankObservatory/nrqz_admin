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

    def handle_row(self, row_data, file_import_attempt):
        applicant, applicant_audit = APPLICANT_FORM_MAP.save_with_audit(
            row_data=row_data, file_import_attempt=file_import_attempt
        )
        contact, contact_audit = CONTACT_FORM_MAP.save_with_audit(
            row_data=row_data, file_import_attempt=file_import_attempt
        )
        case, case_audit = handle_case(
            row_data,
            CASE_FORM_MAP,
            applicant=applicant,
            contact=contact,
            file_import_attempt=file_import_attempt,
        )
        # TODO: If durable?? In the interest of catching _all_ errors...
        if case:
            attachments = handle_attachments(
                row_data,
                case,
                ATTACHMENT_FORM_MAPS,
                file_import_attempt=file_import_attempt,
            )
