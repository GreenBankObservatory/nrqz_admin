from pprint import pprint
from datetime import datetime
import json
import os
from pprint import pformat
import re

import pyexcel
from tqdm import tqdm

from django.db import transaction
from django.db.utils import IntegrityError

from audits.models import BatchAudit, BatchAuditGroup
from cases.models import Attachment, Batch, Case, Facility
from cases.forms import FacilityForm, CaseForm, BatchForm
from .fieldmap import CASE_FORM_MAP, FACILITY_FORM_MAP
from .import_report import ExcelCollectionImportReport, ImportReport
from .strip_excel_non_data import strip_excel_sheet

DEFAULT_DURABLE = False
DEFAULT_THRESHOLD = 0.7
DEFAULT_PREPROCESS = True

EXCEL = "excel"


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


# https://regex101.com/r/gRPTN8/5
nrqz_id_regex_str = r"^(?P<case_num>\d+)(?:[\-\_](?:REV)?(?P<site_num>\d+))?(?:[\s_\*]+(?:\(.*\)[\s_]+)?(?P<site_name>(?:(?:\w+\s+)?\S{5}|\D+))[\s_]+(?P<facility_name>\S+))?"
nrqz_id_regex = re.compile(nrqz_id_regex_str)
nrqz_id_regex_fallback_str = r"^(?P<case_num>\d+).*"
nrqz_id_regex_fallback = re.compile(nrqz_id_regex_fallback_str)


def derive_case_and_site_num_from_nrqz_id(nrqz_id):
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
    return match["case_num"], match["site_num"]


class ExcelCollectionImporter:
    def __init__(
        self,
        paths,
        durable=DEFAULT_DURABLE,
        threshold=DEFAULT_THRESHOLD,
        preprocess=DEFAULT_PREPROCESS,
    ):
        self.paths = sorted(paths)
        self.durable = durable
        self.threshold = threshold
        self.preprocess = preprocess
        self.excel_importers = self._gen_excel_importers(self.paths)
        self.report = ExcelCollectionImportReport(self)

    def _gen_excel_importers(self, paths):
        excel_importers = [
            ExcelImporter(
                path,
                durable=self.durable,
                threshold=self.threshold,
                preprocess=self.preprocess,
            )
            for path in paths
        ]
        return excel_importers

    def process(self):
        longest_filename = (
            max([len(os.path.basename(path)) for path in self.paths])
            if self.paths
            else 0
        )
        progress = tqdm(self.excel_importers, unit="files")
        batch_audits = []
        for excel_importer in progress:
            progress.set_description(
                f"Processing {os.path.basename(excel_importer.path):{longest_filename}}"
            )
            batch_audits.append(excel_importer.process())

        return batch_audits

    # def process_report(self):
    #     self.


class ExcelImporter:
    def __init__(
        self,
        path,
        durable=DEFAULT_DURABLE,
        threshold=DEFAULT_THRESHOLD,
        preprocess=DEFAULT_PREPROCESS,
        batch_audit_group=None,
    ):
        # The path to the Excel file to import
        self.path = path
        # Our import reporter object
        self.report = ImportReport(path)
        self.durable = durable
        self.threshold = threshold
        self.rolled_back = False
        self.preprocess = preprocess
        self.batch_audit_group = batch_audit_group

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
        if self.preprocess:
            tqdm.write("Pre-processing sheet")
            strip_excel_sheet(sheet)

        # Create a new sheet, this time with the column names mapped
        # We couldn't do this before because we weren't sure that our
        # headers were on the first row, but they should be now
        sheet = pyexcel.Sheet(sheet.array, name_columns_by_row=0)
        return sheet.records

    def delete_existing_batch(self):
        existing_batch = self.batch_audit_group.batch
        if existing_batch:
            tqdm.write(
                f"Detected existing batch: {existing_batch} <{existing_batch.id}>; it will be deleted"
            )
            cases_to_delete = existing_batch.cases.all()
            tqdm.write(
                f"Deleting {len(cases_to_delete)} cases: {cases_to_delete.values_list('id', flat=True)}"
            )
            facilities_to_delete = Facility.objects.filter(case__in=cases_to_delete)
            tqdm.write(
                f"Deleting {len(facilities_to_delete)} facilities: {facilities_to_delete.values_list('id', flat=True)}"
            )
            existing_batch.delete()
            for case in cases_to_delete:
                try:
                    case.refresh_from_db()
                except Case.DoesNotExist as error:
                    pass
                else:
                    raise ValueError(f"Failed to delete Case {case}!") from error

            for facility in facilities_to_delete:
                try:
                    facility.refresh_from_db()
                except Facility.DoesNotExist as error:
                    pass
                else:
                    raise ValueError(
                        f"Failed to delete Facility {facility}!"
                    ) from error

    def get_batch_created_on(self):
        """NOTE: Behavior here is OS DEPENDENT!

        https://docs.python.org/3.6/library/os.path.html?highlight=ctime#os.path.getctime
        """

        created_on = datetime.fromtimestamp(os.path.getctime(self.path))
        return created_on

    def get_batch_modified_on(self):
        modified_on = datetime.fromtimestamp(os.path.getmtime(self.path))
        return modified_on

    def create_batch(self):
        if self.batch_audit_group.batch:
            batch_id = self.batch_audit_group.batch.id
            batch_name = self.batch_audit_group.batch.name
        else:
            batch_id = None
            batch_name = os.path.basename(self.path).replace(" ", "_")
        batch_created_on = self.get_batch_created_on()
        batch_modified_on = self.get_batch_modified_on()
        # Purge any existing batch
        self.delete_existing_batch()
        batch_form = BatchForm(
            {
                "id": batch_id,
                "name": batch_name,
                "comments": f"Created by {__file__}",
                "imported_from": self.path,
                "original_created_on": batch_created_on,
                "original_modified_on": batch_modified_on,
                "data_source": EXCEL,
            }
        )
        if batch_form.is_valid():
            batch = batch_form.save()
        else:
            raise BatchRejectionError(
                f"Batch is invalid! {batch_form.errors.as_data()}"
            )
        tqdm.write(f"Created Batch {batch} <{batch.id}>")
        return batch

    @transaction.atomic
    def process(self):
        if not self.batch_audit_group:
            self.batch_audit_group = BatchAuditGroup.objects.create(data_source=EXCEL)
            tqdm.write(f"Created audit_group {self.batch_audit_group}")
        else:
            tqdm.write(
                f"Got audit_group {self.batch_audit_group} linked to {self.batch_audit_group.batch}"
            )

        batch_audit = BatchAudit.objects.create(
            audit_group=self.batch_audit_group,
            errors=self.report.report,
            original_file=self.path,
            error_summary=self.report.generate_error_summary(),
            data_source=EXCEL,
        )
        tqdm.write(
            f"Created batch_audit {batch_audit.id} linked to audit_group {self.batch_audit_group}"
        )
        self._process()

        if self.report.has_fatal_errors():
            # This is a sanity check to ensure that the Batch has in fact been
            # rolled back. Since we are tracking the Batch object inside our
            # import_reporter, we can attempt to refresh it from the DB. We
            # expect that this will fail, but if for some reason it succeeds
            # then we treat this as a fatal error
            try:
                self.batch_audit_group.batch.refresh_from_db()
            except Batch.DoesNotExist:
                tqdm.write(f"Successfully rejected Batch {self.path}")
                # Since the batch was rejected, we must remove it from the
                # BAG, otherwise we'll end up with an IntegrityError
                self.batch_audit_group.batch = None
                self.batch_audit_group.save()
            else:
                raise AssertionError("Batch should have been rolled back, but wasn't!")
            self.rolled_back = True
        else:
            # Similarly, we want to ensure that the Batch has been committed
            # if there are no fatal errors in importing it
            try:
                self.batch_audit_group.batch.refresh_from_db()
            except Batch.DoesNotExist as error:
                raise AssertionError(
                    "Batch should have been committed, but wasn't!"
                ) from error

        if not self.rolled_back:
            if self.report.has_errors():
                status = "created_dirty"
            else:
                status = "created_clean"
        else:
            status = "rejected"

        batch_audit.status = status
        batch_audit.save()

        return batch_audit

    def handle_case(self, row):
        case_form = CASE_FORM_MAP.render(
            row,
            extra={"batch": self.batch_audit_group.batch.id, "data_source": EXCEL},
            allow_unknown=True,
        )
        case_num = case_form["case_num"].value()
        try:
            case = Case.objects.get(case_num=case_num)
        except Case.DoesNotExist:
            if case_form.is_valid():
                case = case_form.save()
            else:
                raise BatchRejectionError(
                    "Case is invalid!", case_form.errors.as_data()
                )
            case_created = True
        else:
            # if not self.durable:
            #     raise DuplicateCaseError("Aw snap we already got a case in there bro")
            # self.report.add_case_error("IntegrityError", "hmmm")
            # self.report.fatal_error_ocurred = True
            case_created = False

        return case, case_created

    def handle_facility(self, row, case):
        # TODO: Alter FacilityForm so that it uses case num instead of ID somehow
        facility_form = FACILITY_FORM_MAP.render(
            row, extra={"case": case.id}, allow_unknown=True
        )
        if facility_form.is_valid():
            facility = facility_form.save()
        else:
            if not self.durable:
                raise BatchRejectionError(
                    "Facility is invalid!", facility_form.errors.as_data()
                )
            row_num = row["Original Row"]
            # TODO: Eliminate the type here; should only be one type of row error
            self.report.add_row_error(
                "validation_error", {"row": row_num, **facility_form.errors.as_data()}
            )
            self.report.fatal_error_ocurred = True
            facility = None
        facility_created = True

        return facility, facility_created

    def handle_row(self, row):
        case, case_created = self.handle_case(row)
        facility, facility_created = self.handle_facility(row, case)
        tqdm.write(f"Case {case_created}: {case}")
        tqdm.write(f"Facility {facility_created}: {facility}")

    # def get_duplicate_headers(self, headers):
    #     # Generate a map of header: from_field for all field_maps
    #     header_field_map = {
    #         header: from_field
    #         for fm in [CASE_FORM_MAP, FACILITY_FORM_MAP]
    #         for from_field, header in fm.unalias(headers).items()
    #     }

    #     if len(set(header_field_map.values())) != len(header_field_map.values()):
    #         dups = {}
    #         for header, from_fields in header_field_map.items():
    #             if to_fields.count(importer.to_field) > 1:
    #                 if importer.to_field in dups:
    #                     dups[importer.to_field].append(header)
    #                 else:
    #                     dups[importer.to_field] = [header]

    #             # There are _a lot_ of sheets that use a blank header as the
    #             # comments column. Generally this is fine, but sometimes there
    #             # is an explicit comments header _and_ a blank header. Since these
    #             # both map to the comments field, we need to reconcile this somehow
    #             # to avoid duplicate detection from being triggered.
    #             # So: If we have detected duplicates in the comments field, AND
    #             # a blank header is one of the duplicates...
    #             if "comments" in dups and "" in dups["comments"]:
    #                 # ...remove it from the comments
    #                 dups["comments"].remove("")

    #         return dups
    #     else:
    #         return None

    @transaction.atomic
    def _process(self):
        """Create objects from given path"""

        self.batch_audit_group.batch = self.create_batch()

        rows = list(self.load_excel_data())
        if not rows:
            if not self.durable:
                raise BatchRejectionError("No rows!")
            else:
                return
        headers = rows[0].keys()

        # If multiple headers map to the same field, report this as an error
        # duplicate_headers = self.get_duplicate_headers(headers)
        # if duplicate_headers:
        #     self.report.set_duplicate_headers(duplicate_headers)

        # If some headers don't map to anything, report this as an error
        known_headers = {
            *CASE_FORM_MAP.get_known_from_fields(),
            *FACILITY_FORM_MAP.get_known_from_fields(),
        }
        unmapped_headers = [header for header in headers if header not in known_headers]
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

        for row in rows:
            try:
                self.handle_row(row)
            except Exception as error:
                if not self.durable:
                    raise BatchRejectionError(
                        "One or more fatal errors has occurred!", error
                    ) from error
                self.report.fatal_error_ocurred = True
            # else:
            #     tqdm.write(f"Successfully created a thing")

        if self.report.has_fatal_errors():
            if not self.durable:
                raise BatchRejectionError("One or more fatal errors ocurred!")
            else:
                tqdm.write("rollback!")
                transaction.set_rollback(True)
