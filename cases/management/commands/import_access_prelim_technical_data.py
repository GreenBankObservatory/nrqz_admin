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

    def handle_row(self, row, batch_import):
        row_data = RowData.objects.create(data=row)
        applicant, applicant_audit = APPLICANT_FORM_MAP.save_with_audit(
            row_data, batch_import=batch_import
        )
        pcase, pcase_audit = handle_case(
            row_data, PCASE_FORM_MAP, applicant=applicant, batch_import=batch_import
        )
        pfacility, pfacility_audit = PFACILITY_FORM_MAP.save_with_audit(
            row_data,
            extra={"pcase": pcase.id if pcase else None},
            batch_import=batch_import,
        )
        audits = {
            "applicant": applicant_audit,
            "pcase": pcase_audit,
            "pfacility": pfacility_audit,
        }
        return audits
