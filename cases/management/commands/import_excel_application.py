"""Import Excel Technical Data"""

import os
from urllib.parse import unquote

import openpyxl
from tqdm import tqdm

from django_import_data import BaseImportCommand


from cases.models import Case
from importers.excel.formmaps import (
    CASE_FORM_MAP,
    FACILITY_FORM_MAP,
    IGNORED_HEADERS,
    ATTACHMENT_FORM_MAPS,
    TAP_FILE_FORM_MAP,
)
from utils.constants import EXCEL
from importers.handlers import handle_attachments, get_or_create_attachment
from importers.excel.strip_excel_non_data import row_is_invalid

DEFAULT_THRESHOLD = 0.7
DEFAULT_PREPROCESS = False


class Command(BaseImportCommand):
    help = "Import Excel Technical Data"

    PROGRESS_TYPE = BaseImportCommand.PROGRESS_TYPES.FILE

    FORM_MAPS = [
        CASE_FORM_MAP,
        FACILITY_FORM_MAP,
        *ATTACHMENT_FORM_MAPS,
        TAP_FILE_FORM_MAP,
    ]
    IGNORED_HEADERS = IGNORED_HEADERS

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "-i",
            "--interactive",
            action="store_true",
            help="If given, drop into an interactive shell upon unhandled exception",
        )
        parser.add_argument(
            "-t",
            "--threshold",
            type=float,
            default=DEFAULT_THRESHOLD,
            help="Threshold of invalid headers which constitute an invalid sheet.",
        )
        parser.add_argument(
            "--no-preprocess",
            default=not DEFAULT_PREPROCESS,
            action="store_true",
            help="Indicate that no pre-processing needs to be done on the given input file(s)",
        )

    def load_rows(self, path):
        """Given path to Excel file, extract data and return"""

        # TODO: This should be defined elsewhere
        primary_sheet = "Working Data"

        if not os.path.isfile(path):
            raise FileNotFoundError(f"{path} does not exist!")
        try:
            # This sheet is used for "values" -- the last-calculated values in each cell
            book_with_values = openpyxl.load_workbook(
                path, read_only=True, data_only=True
            )
            # This workbook is used for hyperlinks only (because they don't appear when doing a "data only" export)
            # We can't get values from this workbook; it stores formulas instead
            book_with_formulas = openpyxl.load_workbook(path)
        except openpyxl.utils.exceptions.InvalidFileException as error:
            raise ValueError(f"{path} must be manually converted to .xlsx!")
        # TODO: this is a file-level error!
        try:
            sheet_with_values = book_with_values[primary_sheet]
            sheet_with_formulas = book_with_formulas[primary_sheet]
        except KeyError:
            raise ValueError(f"'{path}' is missing sheet '{primary_sheet}'")

        # TODO: Re-enable preprocessing
        # if self.preprocess:
        #     tqdm.write("Pre-processing sheet")
        #     strip_excel_sheet(sheet, threshold=self.threshold)
        rows_with_values = sheet_with_values.rows
        rows_with_formulas = sheet_with_formulas.rows

        headers_from_rows_with_values = next(rows_with_values)
        headers_from_rows_with_formulas = next(rows_with_formulas)
        assert len(headers_from_rows_with_values) == len(
            headers_from_rows_with_formulas
        )
        headers = [
            c.value if c.value is not None else ""
            for c in headers_from_rows_with_values
        ]

        # assert len(headers) == len(rows_with_values) == len(rows_with_formulas)
        # num_rows = len(rows_with_values)

        invalid_row_run = 0
        # Create a new sheet, this time with the column names mapped
        # We couldn't do this before because we weren't sure that our
        # headers were on the first row, but they should be now
        duplicate_headers = self.get_duplicate_headers(headers)
        if duplicate_headers:
            raise ValueError(
                f"One or more duplicate headers detected: {duplicate_headers}"
            )

        row_number = 1
        sheet = []
        for row_with_values, row_with_formulas in zip(
            rows_with_values, rows_with_formulas
        ):
            if invalid_row_run > 100:
                tqdm.write(
                    f"More than 100 empty rows in a row! Exiting on row {row_number}!"
                )
                break

            if row_is_invalid(row_with_values):
                invalid_row_run += 1
            else:
                invalid_row_run = 0
                row_dict = {}
                for header, cell_with_values, cell_with_formulas in zip(
                    headers, row_with_values, row_with_formulas
                ):
                    hyperlink = getattr(cell_with_formulas, "hyperlink", None)
                    if hyperlink:
                        value = unquote(hyperlink.target)
                    else:
                        value = cell_with_values.value
                    if header in row_dict:
                        header = f"{header}-1"
                    if header in row_dict:
                        raise ValueError("Whoops")
                    row_dict[header] = value
                sheet.append(row_dict)
            row_number += 1

        return sheet

    def _handle_case(self, row_data):
        # tqdm.write("-" * 80)
        case_form, conversion_errors = CASE_FORM_MAP.render(
            row_data.data, extra={"data_source": EXCEL}, allow_unknown=True
        )
        if not case_form:
            return None, False
        if conversion_errors:
            error_str = f"Failed to convert row for case: {conversion_errors}"
            if self.durable:
                tqdm.write(error_str)
            else:
                raise ValueError(error_str)

        case_num = case_form["case_num"].value()
        try:
            case = Case.objects.get(case_num=case_num)
        except Case.DoesNotExist:
            case, case_audit = CASE_FORM_MAP.save_with_audit(
                row_data=row_data,
                form=case_form,
                extra={"data_source": EXCEL},
                allow_unknown=True,
                imported_by=self.__module__,
            )
            case_created = True
        else:
            # if not self.durable:
            #     raise DuplicateCaseError("Aw snap we already got a case in there bro")
            # self.report.add_case_error("IntegrityError", "hmmm")
            # self.report.fatal_error_ocurred = True
            case_audit = None
            case_created = False

        if case_audit and case_audit.errors:
            tqdm.write(str(case_audit.errors))
        return case, case_created

    def _handle_facility(self, row_data, case):
        # TODO: Alter FacilityForm so that it uses case num instead of ID somehow
        facility, facility_audit = FACILITY_FORM_MAP.save_with_audit(
            extra={"case": case.case_num if case else None},
            allow_unknown=True,
            row_data=row_data,
            imported_by=self.__module__,
        )
        if facility:
            facility_created = True
        else:
            facility_created = False
            tqdm.write("Failed to create facility; here's the audit")
            if facility_audit:
                tqdm.write(str(facility_audit.errors))
            else:
                tqdm.write("No facility audit created")
        return facility, facility_created

    def get_unmapped_headers(self, headers, known_headers):
        possibly_unmapped_headers = super().get_unmapped_headers(headers, known_headers)
        unmapped_headers = []
        for header in possibly_unmapped_headers:
            try:
                int(header)
            except ValueError:
                if header not in known_headers:
                    unmapped_headers.append(header)
        return unmapped_headers

    def handle_record(self, row_data, durable=True):
        case, case_created = self._handle_case(row_data)
        if case_created:
            error_str = "Case should never be created from technical data; only found!"
            if durable:
                row_data.errors.setdefault("case_not_found_errors", [])
                row_data.errors["case_not_found_errors"].append(error_str)
                row_data.save()
            else:
                raise ValueError(error_str)
        facility, facility_created = self._handle_facility(row_data, case)

        if facility:
            attachments = handle_attachments(
                row_data=row_data,
                model=facility,
                form_maps=ATTACHMENT_FORM_MAPS,
                imported_by=self.__module__,
            )
            propagation_study, attachment_created = get_or_create_attachment(
                row_data=row_data,
                form_map=TAP_FILE_FORM_MAP,
                imported_by=self.__module__,
            )
            facility.propagation_study = propagation_study
            facility.save()
            if propagation_study:
                facility.attachments.add(propagation_study)
