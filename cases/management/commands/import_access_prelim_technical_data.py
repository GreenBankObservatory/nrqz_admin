from importers.handlers import handle_case
from importers.access_prelim_technical.fieldmap import (
    APPLICANT_FORM_MAP,
    PCASE_FORM_MAP,
    PFACILITY_FORM_MAP,
)
from ._base_import import BaseImportCommand


class Command(BaseImportCommand):
    help = "Import Access Preliminary Technical Data"

    def handle_row(self, row):
        applicant = APPLICANT_FORM_MAP.save(row)
        pcase, __ = handle_case(row, PCASE_FORM_MAP, applicant=applicant)
        PFACILITY_FORM_MAP.save(row, extra={"pcase": pcase.id})
