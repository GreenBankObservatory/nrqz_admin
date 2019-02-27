from importers.handlers import get_or_create_attachment, handle_case
from importers.access_prelim_technical.fieldmap import (
    APPLICANT_FORM_MAP,
    PCASE_FORM_MAP,
    PFACILITY_FORM_MAP,
    PROPAGATION_STUDY_FORM_MAP,
    IGNORED_HEADERS,
)
from django_import_data import BaseImportCommand
from django_import_data.models import RowData


class Command(BaseImportCommand):
    help = "Import Access Preliminary Technical Data"

    PROGRESS_TYPE = BaseImportCommand.PROGRESS_TYPES.ROW

    # TODO: This is somewhat stupid; think of a better way
    FORM_MAPS = [
        APPLICANT_FORM_MAP,
        PCASE_FORM_MAP,
        PFACILITY_FORM_MAP,
        PROPAGATION_STUDY_FORM_MAP,
    ]
    IGNORED_HEADERS = IGNORED_HEADERS

    def handle_record(self, row_data, file_import_attempt, durable=True):
        applicant, applicant_audit = APPLICANT_FORM_MAP.save_with_audit(
            row_data,
            file_import_attempt=file_import_attempt,
            imported_by=self.__module__,
        )
        pcase, pcase_created = handle_case(
            row_data,
            PCASE_FORM_MAP,
            applicant=applicant,
            file_import_attempt=file_import_attempt,
            imported_by=self.__module__,
        )
        if pcase_created:
            error_str = "PCase should never be created from technical data; only found!"
            if durable:
                row_data.errors.setdefault("case_not_found_errors", [])
                row_data.errors["case_not_found_errors"].append(error_str)
                row_data.save()
            else:
                raise ValueError(error_str)
        pfacility, pfacility_audit = PFACILITY_FORM_MAP.save_with_audit(
            row_data,
            extra={"pcase": pcase.id if pcase else None},
            file_import_attempt=file_import_attempt,
            imported_by=self.__module__,
        )
        if pfacility:
            propagation_study, created = get_or_create_attachment(
                row_data,
                PROPAGATION_STUDY_FORM_MAP,
                file_import_attempt=file_import_attempt,
                imported_by=self.__module__,
            )
            pfacility.propagation_study = propagation_study
            pfacility.save()
            if propagation_study:
                pfacility.attachments.add(propagation_study)
