"""Import Access Technical Data"""

from importers.handlers import get_or_create_attachment, handle_case
from importers.access_technical.formmaps import (
    APPLICANT_FORM_MAP,
    CASE_FORM_MAP,
    FACILITY_FORM_MAP,
    PROPAGATION_STUDY_FORM_MAP,
    IGNORED_HEADERS,
)
from django_import_data import BaseImportCommand


class Command(BaseImportCommand):
    help = "Import Access Technical Data"

    PROGRESS_TYPE = BaseImportCommand.PROGRESS_TYPES.ROW
    # TODO: This is somewhat stupid; think of a better way
    FORM_MAPS = [
        APPLICANT_FORM_MAP,
        CASE_FORM_MAP,
        FACILITY_FORM_MAP,
        PROPAGATION_STUDY_FORM_MAP,
    ]
    IGNORED_HEADERS = IGNORED_HEADERS

    def handle_record(self, row_data, durable=True):
        applicant, applicant_audit = APPLICANT_FORM_MAP.save_with_audit(
            row_data, imported_by=self.__module__
        )
        case, case_created = handle_case(
            row_data, CASE_FORM_MAP, applicant=applicant, imported_by=self.__module__
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
            extra={"case": case.case_num if case else None},
            imported_by=self.__module__,
        )
        if facility:
            propagation_study, created = get_or_create_attachment(
                row_data, PROPAGATION_STUDY_FORM_MAP, imported_by=self.__module__
            )
            facility.propagation_study = propagation_study
            facility.save()
            if propagation_study:
                facility.attachments.add(propagation_study)
