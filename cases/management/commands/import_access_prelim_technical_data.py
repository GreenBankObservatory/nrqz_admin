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

    def handle_row(self, row):
        row_data = RowData.objects.create(data=row)
        applicant, applicant_audit = APPLICANT_FORM_MAP.save_with_audit(
            row, row_data=row_data
        )
        pcase, pcase_audit = handle_case(
            row, PCASE_FORM_MAP, applicant=applicant, row_data=row_data
        )
        pfacility, pfacility_audit = PFACILITY_FORM_MAP.save_with_audit(
            row, extra={"pcase": pcase.id if pcase else None}, row_data=row_data
        )
        audits = {
            "applicant": applicant_audit,
            "pcase": pcase_audit,
            "pfacility": pfacility_audit,
        }
        return audits
