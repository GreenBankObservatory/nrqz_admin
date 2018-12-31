"""Import Access Technical Data"""

from importers.handlers import handle_case
from importers.access_technical.fieldmap import (
    APPLICANT_FORM_MAP,
    CASE_FORM_MAP,
    FACILITY_FORM_MAP,
)
from ._base_import import BaseImportCommand


class Command(BaseImportCommand):
    help = "Import Access Technical Data"

    def handle_row(self, row):
        applicant = APPLICANT_FORM_MAP.save(row)
        case, __ = handle_case(row, CASE_FORM_MAP, applicant=applicant)
        FACILITY_FORM_MAP.save(row, extra={"case": case.id})
