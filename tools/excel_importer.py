import json
import os
from pprint import pformat
import re

import pyexcel
from tqdm import tqdm

from django.db import transaction
from django.db.utils import IntegrityError


from cases.models import Attachment, Batch, Case, Facility
from cases.forms import FacilityForm
from tools.excelfieldmap import (
    facility_field_map,
    gen_header_field_map,
    get_unmapped_headers,
)
from tools.import_report import ExcelCollectionImportReport, ImportReport


DEFAULT_DURABLE = False
DEFAULT_THRESHOLD = 0.7


class BatchImportException(Exception):
    pass


class BatchImportError(BatchImportException):
    pass


class BatchRejectionError(BatchImportError):
    pass


class DuplicateCaseError(BatchRejectionError):
    pass


class UnmappedFieldError(BatchRejectionError):
    pass


class MissingNrqzIdError(BatchRejectionError):
    pass


class FacilityValidationError(BatchRejectionError):
    pass


class TooManyUnmappedHeadersError(BatchRejectionError):
    pass


# https://regex101.com/r/gRPTN8/1
nrqz_id_regex_str = r"^(?P<case_num>\d+)[\s_\*]+(?:\(.*\)[\s_]+)?(?P<site_name>(?:(?:\w+\s+)?\S{5}|\D+))[\s_]+(?P<facility_name>\S+)$"
nrqz_id_regex = re.compile(nrqz_id_regex_str)
nrqz_id_regex_fallback_str = r"^(?P<case_num>\d+).*"
nrqz_id_regex_fallback = re.compile(nrqz_id_regex_fallback_str)


def derive_case_num_from_nrqz_id(nrqz_id):
    try:
        match = nrqz_id_regex.match(nrqz_id)
    except TypeError:
        tqdm.write(f"nrqz_id: {nrqz_id!r}")
        raise

    if not match:
        match = nrqz_id_regex_fallback.match(nrqz_id)
        if not match:
            raise ValueError(
                f"Could not parse NRQZ ID '{nrqz_id}' using "
                f"'{nrqz_id_regex_str}' or '{nrqz_id_regex_fallback_str}'!"
            )
    return match["case_num"]


class ExcelCollectionImporter:
    def __init__(self, paths, durable=DEFAULT_DURABLE, threshold=DEFAULT_THRESHOLD):
        self.paths = sorted(paths)
        self.durable = durable
        self.threshold = threshold
        self.excel_importers = self._gen_excel_importers(self.paths)
        self.report = ExcelCollectionImportReport(self)

    def _gen_excel_importers(self, paths):
        excel_importers = [
            ExcelImporter(path, durable=self.durable, threshold=self.threshold)
            for path in paths
        ]
        return excel_importers

    def process(self):

        longest_filename = max([len(os.path.basename(path)) for path in self.paths])
        progress = tqdm(self.excel_importers, unit="files")
        for excel_importer in progress:
            progress.set_description(
                f"Processing {os.path.basename(excel_importer.path):{longest_filename}}"
            )

            try:
                excel_importer.process()
            except BatchRejectionError as error:
                # This is a sanity check to ensure that the Batch has in fact been
                # rolled back. Since we are tracking the Batch object inside our
                # import_reporter, we can attempt to refresh it from the DB. We
                # expect that this will fail, but if for some reason it succeeds
                # then we treat this as a fatal error
                try:
                    excel_importer.batch.refresh_from_db()
                except Batch.DoesNotExist:
                    tqdm.write(
                        f"Successfully rejected Batch {excel_importer.path}: {error}"
                    )
                else:
                    raise ValueError("Batch should have been rolled back, but wasn't!")
                excel_importer.rolled_back = True
            else:
                # Similarly, we want to ensure that the Batch has been committed
                # if there are no fatal errors in importing it
                try:
                    excel_importer.batch.refresh_from_db()
                except Batch.DoesNotExist as error:
                    raise ValueError(
                        "Batch should have been committed, but wasn't!"
                    ) from error

    # def process_report(self):
    #     self.


class ExcelImporter:
    def __init__(self, path, durable=DEFAULT_DURABLE, threshold=DEFAULT_THRESHOLD):
        # The path to the Excel file to import
        self.path = path
        # The Batch representation of the Excel file
        self.batch = None
        # Our import reporter object
        self.report = ImportReport(path)
        self.durable = durable
        self.threshold = threshold
        self.rolled_back = False

    def load_excel_data(self):
        """Given path to Excel file, extract data and return"""

        book = pyexcel.get_book(file_name=self.path)

        primary_sheet = "Working Data"

        try:
            sheet = book.sheet_by_name(primary_sheet)
        except KeyError:
            sheet = book.sheet_by_index(0)
            self.report.add_sheet_name_error(
                f"Sheet {primary_sheet!r} not found; used first sheet instead: {sheet.name!r}"
            )

        # try:
        #     from_applicant = book.sheet_by_name("From Applicant")
        # except KeyError:
        #     import ipdb

        #     ipdb.set_trace()

        # sheet = working_data
        return sheet.array

    def create_facility_dict_from_row(self, header_field_map, row, row_num):

        facility_dict = {}
        for header, importer, cell in zip(
            header_field_map.keys(), header_field_map.values(), row
        ):
            if importer and importer.to_field:
                try:
                    facility_dict[importer.to_field] = importer.converter(cell)
                except (ValueError) as error:
                    self.report.add_row_error(
                        "conversion_error",
                        {
                            "row": row_num,
                            "header": header,
                            "converter": importer.converter.__name__,
                            "field": importer.to_field,
                            "error": str(error),
                            "value": cell,
                        },
                    )
            else:
                # tqdm.write(
                #     "Either no field importer or no importer.to_field; skipping "
                #     f"value {cell!r} for header {header!r}!"
                # )
                continue

        return facility_dict

    def get_duplicate_headers(self, header_field_map):
        to_fields = [
            importer.to_field for importer in header_field_map.values() if importer
        ]

        if len(set(to_fields)) != len(to_fields):
            dups = {}
            for header, importer in header_field_map.items():
                if importer and to_fields.count(importer.to_field) > 1:
                    if importer.to_field in dups:
                        dups[importer.to_field].append(header)
                    else:
                        dups[importer.to_field] = [header]

                # There are _a lot_ of sheets that use a blank header as the
                # comments column. Generally this is fine, but sometimes there
                # is an explicit comments header _and_ a blank header. Since these
                # both map to the comments field, we need to reconcile this somehow
                # to avoid duplicate detection from being triggered.
                # So: If we have detected duplicates in the comments field, AND
                # a blank header is one of the duplicates...
                if "comments" in dups and "" in dups["comments"]:
                    # ...remove it from the comments
                    dups["comments"].remove("")

            return dups
        else:
            return None

    @staticmethod
    def derive_nrqz_id_field(header_field_map):
        to_fields = [fm.to_field for fm in header_field_map.values() if fm]
        nrqz_id_fields = ["nrqz_id", "site_name"]
        for nrqz_id_field in nrqz_id_fields:
            if nrqz_id_field in to_fields:
                return nrqz_id_field

        return None

    @staticmethod
    def get_unmapped_fields():
        excluded_fields = ["location", "asr_is_from_applicant", "case", "structure"]
        facility_fields = [
            field for field in FacilityForm.Meta.fields if field not in excluded_fields
        ]

        mapped_fields = [
            importer.to_field
            for importer in facility_field_map.values()
            if importer is not None
        ]
        unmapped_fields = [
            field for field in facility_fields if field not in mapped_fields
        ]
        return unmapped_fields

    @transaction.atomic
    def create_facility(self, facility_dict, case):
        self.report.facilities_processed += 1
        # TODO: Alter FacilityForm so that it uses case num instead of ID somehow
        facility_dict = {**facility_dict, "case": case.id if case else None}
        facility_form = FacilityForm(facility_dict)
        if facility_form.is_valid():
            facility = facility_form.save()
            self.report.audit_facility_success(facility)
            self.report.facilities_created.append(facility)
            return None
        else:
            if self.durable:
                self.report.audit_facility_error(
                    case, facility_dict, facility_form.errors.as_data()
                )
            else:
                raise FacilityValidationError(
                    f"Facility {facility_dict} failed validation:\n{pformat(facility_form.errors.as_data())}"
                )

            self.report.facilities_not_created.append(facility_dict)
            useful_errors = {
                field: {"value": facility_dict[field], "errors": errors}
                for field, errors in facility_form.errors.as_data().items()
            }
            return useful_errors

    @transaction.atomic
    def create_case(self, case_num, row_to_facility_map):
        self.report.cases_processed += 1
        # Create the case...
        try:
            case = Case.objects.create(batch=self.batch, case_num=case_num)
        # ...or report an error if we can't
        except IntegrityError as error:
            dce = DuplicateCaseError(
                f"Batch '{self.batch}' rejected due to duplicate case: {case_num}"
            )
            self.report.add_case_error("IntegrityError", error)
            self.report.cases_not_created.append(case_num)
            if not self.durable:
                raise dce from error
            case = None
        # If the case is created, we now need to create all of its Facilities
        else:
            self.report.cases_created.append(case)
        # For every Facility dict...
        for row_num, facility_dict in row_to_facility_map.items():
            facility_errors = self.create_facility(facility_dict, case)
            if facility_errors:
                self.report.add_row_error(
                    "validation_error", {"row": row_num, "error": facility_errors}
                )

    @transaction.atomic
    def create_batch(self):
        # A Batch representing this Excel file
        batch = Batch.objects.create(
            name=os.path.basename(self.path), comments=f"Created by {__file__}"
        )
        self.batch = batch

        # An attachment referencing the original Excel (or .csv) file
        batch.attachments.add(
            Attachment.objects.create(
                path=self.path, comments=f"Attached by {__file__}"
            )
        )

        return batch

    def create_case_map(self, header_field_map, data, nrqz_id_field):
        """Create map of { case_num: { row_num: facility_dict } } and return"""

        case_map = {}
        for row in data:
            # Pull out the row number from the row...
            row_num = row[-1]
            try:
                row_num = int(row_num)
            except ValueError:
                self.report.add_row_error(
                    "invalid_row_num",
                    {
                        "row": row_num,
                        "error": f"Could not convert {row_num} to a number! Check original Excel file for issues",
                    },
                )
            facility_dict = self.create_facility_dict_from_row(
                header_field_map, row, row_num
            )
            # Derive the case number from the NRQZ ID (or Site Name, if no NRQZ ID found earlier)
            try:
                case_num = derive_case_num_from_nrqz_id(
                    str(facility_dict[nrqz_id_field])
                )
            except ValueError as error:
                # If there's an error...
                field_header_map = {
                    value.to_field: key
                    for key, value in header_field_map.items()
                    if value is not None
                }
                header = field_header_map[nrqz_id_field]
                # ...consider it a "data" error and report it
                self.report.add_row_error(
                    "nrqz_id_error",
                    {
                        "row": row_num,
                        "header": header,
                        "error": str(error),
                        "value": facility_dict[nrqz_id_field],
                    },
                )
            else:
                # If there's not an error, add the new facility_dict to our case_dict
                if case_num in case_map:
                    case_map[case_num][row_num] = facility_dict
                else:
                    case_map[case_num] = {row_num: facility_dict}

        return case_map

    def process_case_map(self, case_map):
        for case_num, row_to_facility_map in case_map.items():
            self.create_case(case_num, row_to_facility_map)

    @transaction.atomic
    def process(self):
        """Create objects from given path"""

        self.create_batch()

        rows = self.load_excel_data()
        # A list of the headers actually in the file
        headers = rows[0][:-1]
        # A list of rows containing data
        data = rows[1:]
        # Generate a map of headers to field importers
        header_field_map = gen_header_field_map(headers)
        # If multiple headers map to the same field, report this as an error
        duplicate_headers = self.get_duplicate_headers(header_field_map)
        if duplicate_headers:
            self.report.set_duplicate_headers(duplicate_headers)

        # If some headers don't map to anything, report this as an error
        unmapped_headers = get_unmapped_headers(header_field_map)
        if unmapped_headers:
            self.report.set_unmapped_headers(unmapped_headers)

        unmapped_header_ratio = len(unmapped_headers) / len(headers)
        if unmapped_header_ratio > self.threshold:
            self.report.add_too_many_unmapped_headers_error(
                f"{unmapped_header_ratio * 100:.2f}% of headers are not mapped; batch rejected"
            )
            if not self.durable:
                raise TooManyUnmappedHeadersError(
                    f"{unmapped_header_ratio * 100:.2f}% of headers are not mapped; batch rejected"
                )

        unmapped_fields = self.get_unmapped_fields()
        if unmapped_fields:
            self.report.set_unmapped_fields(unmapped_fields)
            if not self.durable:
                raise UnmappedFieldError(
                    f"Batch '{self.batch}' rejected due to unmapped DB fields: {unmapped_fields}"
                )

        # Determine the field in which our NRQZ ID string has been stored
        # This will be used later to parse out the case number
        nrqz_id_field = self.derive_nrqz_id_field(header_field_map)
        if nrqz_id_field:
            # Create our case->row_num->facility map
            case_map = self.create_case_map(header_field_map, data, nrqz_id_field)
            # Create all Cases and Facilities in the case_map
            self.process_case_map(case_map)
        else:
            self.report.add_case_error(
                "MissingNrqzIdError", MissingNrqzIdError("Could not derive NRQZ ID!")
            )
            if not self.durable:
                raise MissingNrqzIdError("Could not derive NRQZ ID!")

        if self.report.report:
            error_summary = self.report.get_non_fatal_errors()
            self.batch.import_error_summary = json.dumps(error_summary, indent=2)
            tqdm.write(self.path)
            tqdm.write(self.batch.import_error_summary)
            self.batch.save()

        if self.report.has_fatal_errors():
            raise BatchRejectionError("One or more fatal errors has occurred!")

        return self.report
