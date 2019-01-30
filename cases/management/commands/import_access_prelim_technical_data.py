from importers.handlers import handle_case
from importers.access_prelim_technical.fieldmap import (
    APPLICANT_FORM_MAP,
    PCASE_FORM_MAP,
    PFACILITY_FORM_MAP,
)
from django_import_data import BaseImportCommand
from django_import_data.models import RowData


class Command(BaseImportCommand):
    help = "Import Access Preliminary Technical Data"

    def handle_record(self, row_data, file_import_attempt):
        applicant, applicant_audit = APPLICANT_FORM_MAP.save_with_audit(
            row_data, file_import_attempt=file_import_attempt
        )
        pcase, pcase_audit = handle_case(
            row_data,
            PCASE_FORM_MAP,
            applicant=applicant,
            file_import_attempt=file_import_attempt,
        )
        pfacility, pfacility_audit = PFACILITY_FORM_MAP.save_with_audit(
            row_data,
            extra={"pcase": pcase.id if pcase else None},
            file_import_attempt=file_import_attempt,
        )
