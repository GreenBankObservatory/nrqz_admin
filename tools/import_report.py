import json
from collections import namedtuple, OrderedDict
from pprint import pprint


class ImportReport:
    def __init__(self, filename):
        self.filename = filename

        self.facilities_processed = 0
        self.facilities_created = []
        self.facilities_not_created = []
        self.cases_processed = 0
        self.cases_created = []
        self.cases_not_created = []

        self.report = {}

        self.fatal_errors = {
            "batch_errors": "__all__",
            "sheet_errors": [
                "duplicate_headers",
                "unmapped_fields",
                "too_many_unmapped_headers",
            ],
            "case_errors": "__all__",
            "row_errors": "__all__",
        }

        self.batch_audit = {}
        self.batch = None

    def audit_facility_error(self, case, facility_dict, facility_errors):
        if case in self.batch_audit:
            self.batch_audit[case].append((facility_dict, facility_errors))
        else:
            self.batch_audit[case] = [(facility_dict, facility_errors)]

    def audit_facility_success(self, facility):
        case = facility.case

        if case in self.batch_audit:
            self.batch_audit[case].append((facility, None))
        else:
            self.batch_audit[case] = [(facility, None)]

    def audit_case(batch_name, case_num, case_errors):
        pass

    def audit_batch(batch_name, batch_errors):
        pass

    def _add_simple_error(self, name, error_type, error):
        if name not in self.report:
            self.report[name] = {}

        if error_type not in self.report[name]:
            self.report[name][error_type] = [error]
        else:
            self.report[name][error_type].append(error)

    def _set_simple_error(self, name, error_type, error):
        if name not in self.report:
            self.report[name] = {}

        if error_type not in self.report[name]:
            self.report[name][error_type] = error

    # def add_facility_error(self, error):
    #     self._add_simple_error("facility_errors", error)

    def add_case_error(self, error_type, error):
        self._add_simple_error("case_errors", error_type, error)

    def add_batch_error(self, error_type, error):
        self._add_simple_error("batch_errors", error_type, error)

    def add_sheet_name_error(self, error):
        self._add_simple_error("sheet_errors", "sheet_name_error", error)

    def set_unmapped_headers(self, headers):
        self._set_simple_error("sheet_errors", "unmapped_headers", headers)

    def set_unmapped_fields(self, fields):
        self._set_simple_error("sheet_errors", "unmapped_fields", fields)

    def set_duplicate_headers(self, headers):
        self._set_simple_error("sheet_errors", "duplicate_headers", headers)

    def add_too_many_unmapped_headers_error(self, error):
        self._add_simple_error("sheet_errors", "too_many_unmapped_headers", error)

    def add_row_error(self, error_type, error):
        self._add_simple_error("row_errors", error_type, error)

    # def add_row_error(self, row_num, error_type, error):
    #     if row_num not in self.report["row_errors"]:
    #         self.report["row_errors"][row_num] = {}

    #     self.report["row_errors"][row_num][error_type] = error

    def generate_error_summary(self):
        """Generate a more concise error report"""

        error_summary = {}
        error_summary["unmapped_headers"] = self.report["sheet_errors"][
            "unmapped_headers"
        ]

        # column_error_summary = {}
        # for row_num, errors_by_type in self.report["row_errors"].items():
        #     for error_type, row_errors in errors_by_type.items():
        #         for field, row_error in row_errors.items():

        #             if field in column_error_summary:
        #                 if (
        #                     row_error["value"]
        #                     not in column_error_summary[field]["Invalid Values"]
        #                 ):
        #                     column_error_summary[field]["Invalid Values"].append(
        #                         str(row_error["value"])
        #                     )
        #             else:
        #                 column_error_summary[field] = OrderedDict(
        #                     (
        #                         ("Field", field),
        #                         ("Invalid Values", [str(row_error["value"])]),
        #                     )
        #                 )
        # if column_error_summary:
        #     error_summary["Column Errors"] = sorted(
        #         column_error_summary.values(), key=lambda x: x["Field"]
        #     )

        return error_summary

    def has_errors(self, report=None):
        if report is None:
            report = self.report
        for errors_by_type in report.values():
            for error in errors_by_type.values():
                if any(error):
                    return True

        return False

    def get_non_fatal_errors(self):
        non_fatal_errors = {}
        for error_category, errors_by_type in self.report.items():
            for error_type, errors in errors_by_type.items():
                if error_category not in self.fatal_errors or (
                    error_type not in self.fatal_errors[error_category]
                    and self.fatal_errors[error_category] != "__all__"
                ):
                    if error_category not in non_fatal_errors:
                        non_fatal_errors[error_category] = {}

                    non_fatal_errors[error_category][error_type] = errors

        return non_fatal_errors

    def get_fatal_errors(self):
        fatal_errors = {}
        for error_category, errors_by_type in self.report.items():
            for error_type, errors in errors_by_type.items():
                if (
                    # The category must be in fatal errors, otherwise it can't be an error
                    error_category in self.fatal_errors
                    and (
                        # Similarly, the error type must be in the category
                        error_type in self.fatal_errors[error_category]
                        # or the error types must be set to all
                        or self.fatal_errors[error_category] == "__all__"
                    )
                ):
                    if error_category not in fatal_errors:
                        fatal_errors[error_category] = {}

                    fatal_errors[error_category][error_type] = errors

        return fatal_errors

    def has_fatal_errors(self):
        return self.has_errors(self.get_fatal_errors())

    # def summarize_fatal_errors(self):
    #     return {
    #         self.report["batch_errors"]
    #         self.report["sheet_errors"]["duplicate_headers"]
    #         self.report["sheet_errors"]["unmapped_fields"]
    #         self.report["sheet_errors"]["too_many_unmapped_headers"]
    #         self.report["case_errors"]
    #         self.report["row_errors"]
    #     }

    # def batch_has_fatal_errors(self):
    #     for error_category, fatal_types in fatal_errors.items():
    #         if fatal_types != "__all__":
    #             try:
    #                 if any([self.report[error_type][fatal_type] for fatal_type in fatal_types if error_type in self.report and ]):
    #                     return True
    #             except KeyError:
    #                 pass

    #     return False
