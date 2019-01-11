"""Import Access Technical Data"""

from importers.handlers import handle_case
from importers.access_technical.fieldmap import (
    APPLICANT_FORM_MAP,
    CASE_FORM_MAP,
    FACILITY_FORM_MAP,
)
from django_import_data import BaseImportCommand
from django_import_data.models import RowData


class Command(BaseImportCommand):
    help = "Import Access Technical Data"

    def handle_row(self, row, batch_import):
        row_data = RowData.objects.create(data=row)
        applicant, applicant_audit = APPLICANT_FORM_MAP.save_with_audit(
            row_data, batch_import=batch_import
        )
        case, case_audit = handle_case(
            row_data, CASE_FORM_MAP, applicant=applicant, batch_import=batch_import
        )
        facility, facility_audit = FACILITY_FORM_MAP.save_with_audit(
            row_data,
            extra={"case": case.id if case else None},
            batch_import=batch_import,
        )
        audits = {
            "applicant": applicant_audit,
            "case": case_audit,
            "facility": facility_audit,
        }
        return audits
