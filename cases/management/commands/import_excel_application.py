"""Import Excel Technical Data"""

import pyexcel
from tqdm import tqdm

from django_import_data import BaseImportCommand


from cases.models import Case
from importers.excel.fieldmap import CASE_FORM_MAP, FACILITY_FORM_MAP
from utils.constants import EXCEL

DEFAULT_THRESHOLD = 0.7
DEFAULT_PREPROCESS = False


class Command(BaseImportCommand):
    help = "Import Excel Technical Data"

    PROGRESS_TYPE = BaseImportCommand.PROGRESS_TYPES.FILE

    FORM_MAPS = [CASE_FORM_MAP, FACILITY_FORM_MAP]

    IGNORED_HEADERS = ["Original Row"]

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

    @staticmethod
    def load_rows(path):
        """Given path to Excel file, extract data and return"""

        book = pyexcel.get_book(file_name=path)

        # TODO: This should be defined elsewhere
        primary_sheet = "Working Data"

        try:
            sheet = book.sheet_by_name(primary_sheet)
        except KeyError:
            # TODO: this is a file-level error!
            raise ValueError(f"Sheet {primary_sheet!r} not found!")

        # TODO: Re-enable preprocessing
        # if self.preprocess:
        #     tqdm.write("Pre-processing sheet")
        #     strip_excel_sheet(sheet, threshold=self.threshold)

        # Create a new sheet, this time with the column names mapped
        # We couldn't do this before because we weren't sure that our
        # headers were on the first row, but they should be now
        sheet = pyexcel.Sheet(sheet.array, name_columns_by_row=0)
        return sheet.records

    def _handle_case(self, row_data, file_import_attempt):
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
                file_import_attempt=file_import_attempt,
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

    def _handle_facility(self, row_data, case, file_import_attempt):
        # TODO: Alter FacilityForm so that it uses case num instead of ID somehow
        facility, facility_audit = FACILITY_FORM_MAP.save_with_audit(
            extra={"case": case.id if case else None},
            allow_unknown=True,
            row_data=row_data,
            file_import_attempt=file_import_attempt,
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

    def handle_record(self, row_data, file_import_attempt):
        case, case_created = self._handle_case(
            row_data, file_import_attempt=file_import_attempt
        )
        facility, facility_created = self._handle_facility(
            row_data, case, file_import_attempt=file_import_attempt
        )

        if not case or not facility:
            tqdm.write("-" * 80)
