"""Import Access Technical Data"""

from importers.handlers import handle_attachments, handle_case
from importers.access_technical.fieldmap import (
    APPLICANT_FORM_MAP,
    CASE_FORM_MAP,
    FACILITY_FORM_MAP,
    ATTACHMENT_FORM_MAP,
)
from django_import_data import BaseImportCommand
from django_import_data.models import RowData


class Command(BaseImportCommand):
    help = "Import Access Technical Data"

    PROGRESS_TYPE = BaseImportCommand.PROGRESS_TYPES.ROW
    # TODO: This is somewhat stupid; think of a better way
    FORM_MAPS = [
        APPLICANT_FORM_MAP,
        CASE_FORM_MAP,
        FACILITY_FORM_MAP,
        ATTACHMENT_FORM_MAP,
    ]

    def handle_record(self, row_data, file_import_attempt, durable=True):
        applicant, applicant_audit = APPLICANT_FORM_MAP.save_with_audit(
            row_data,
            file_import_attempt=file_import_attempt,
            imported_by=self.__module__,
        )
        case, case_created = handle_case(
            row_data,
            CASE_FORM_MAP,
            applicant=applicant,
            file_import_attempt=file_import_attempt,
            imported_by=self.__module__,
        )
        if case_created:
            error_str = "PCase should never be created from technical data; only found!"
            if durable:
                row_data.errors.setdefault("case_not_found_errors", [])
                row_data.errors["case_not_found_errors"].append(error_str)
                row_data.save()
            else:
                raise ValueError(error_str)
        facility, facility_audit = FACILITY_FORM_MAP.save_with_audit(
            row_data,
            extra={"case": case.id if case else None},
            file_import_attempt=file_import_attempt,
            imported_by=self.__module__,
        )

        attachments = handle_attachments(
            row_data,
            facility,
            [ATTACHMENT_FORM_MAP],
            file_import_attempt=file_import_attempt,
            imported_by=self.__module__,
        )
