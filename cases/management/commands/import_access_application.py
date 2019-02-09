"""Import Access Application Data"""

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

    PROGRESS_TYPE = BaseImportCommand.PROGRESS_TYPES.ROW

    # TODO: This is somewhat stupid; think of a better way
    FORM_MAPS = [
        APPLICANT_FORM_MAP,
        CONTACT_FORM_MAP,
        CASE_FORM_MAP,
        *ATTACHMENT_FORM_MAPS,
    ]

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
