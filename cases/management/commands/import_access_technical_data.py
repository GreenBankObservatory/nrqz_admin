"""Import Access Technical Data"""

from importers.handlers import handle_case
from importers.access_technical.fieldmap import (
    APPLICANT_FORM_MAP,
    CASE_FORM_MAP,
    FACILITY_FORM_MAP,
)
from django_import_data import BaseImportCommand
from django_import_data.models import RowAudit


class Command(BaseImportCommand):
    help = "Import Access Technical Data"

    def handle_row(self, row):
        row_audit = RowAudit.objects.create(data=row)
        applicant, applicant_audit = APPLICANT_FORM_MAP.save_with_audit(
            row, row_audit=row_audit
        )
        case, case_audit = handle_case(
            row, CASE_FORM_MAP, applicant=applicant, row_audit=row_audit
        )
        facility, facility_audit = FACILITY_FORM_MAP.save_with_audit(
            row, extra={"case": case.id if case else None}, row_audit=row_audit
        )
        audits = {
            "applicant": applicant_audit,
            "case": case_audit,
            "facility": facility_audit,
        }
        return audits
