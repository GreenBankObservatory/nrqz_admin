import json
from collections import namedtuple, OrderedDict
from pprint import pformat


def format_total(num_created, num_processed):
    return f"{num_created}/{num_processed} " f"({(num_created/num_processed)*100:.3f}%)"


class ExcelCollectionImportReport:
    def __init__(self, excel_collection_importer):
        self.excel_collection_importer = excel_collection_importer
        self.import_reporters = [
            ei.report for ei in self.excel_collection_importer.excel_importers
        ]

    def print_summary(self, summary):
        print("Summary:")
        for error_category, errors_by_type in summary.items():
            print(f"  Summary of ALL {error_category!r}:")
            for error_type, errors_ in errors_by_type.items():
                print(f"    Unique {error_type!r}:")
                for error_ in sorted([str(e) for e in errors_]):
                    formatted_error = "\n".join(
                        [f"      {line}" for line in pformat(error_).split("\n")]
                    )
                    print(formatted_error)

    def print_report(self):
        print("Report:")
        for import_reporter in self.import_reporters:
            fatal_errors = import_reporter.get_fatal_errors()
            if import_reporter.has_errors(fatal_errors):
                print(f"  Batch {import_reporter.filename} rejected:")
                for error_category, errors_by_type in fatal_errors.items():
                    print(f"    {error_category!r} errors by type:")
                    for error_type, errors_ in errors_by_type.items():
                        print(f"      {error_type!r}:")
                        for error_ in errors_:
                            formatted_error = "\n".join(
                                [
                                    f"        {line}"
                                    for line in pformat(error_).split("\n")
                                ]
                            )
                            print(formatted_error)
            else:
                non_fatal_errors = import_reporter.get_non_fatal_errors()
                if import_reporter.has_errors(non_fatal_errors):
                    print(
                        f"  Batch {import_reporter.filename} created with the following caveats:"
                    )
                    formatted_summary = "\n".join(
                        [
                            f"        {line}"
                            for line in pformat(non_fatal_errors).split("\n")
                        ]
                    )
                    print(formatted_summary)
                else:
                    print(
                        f"  Batch {import_reporter.filename} created without any issues"
                    )

    def print_totals(self, totals):
        print("Totals:")

        print("  Batches:")
        formatted_batches = format_total(
            totals["batches"]["created"], totals["batches"]["processed"]
        )
        print(f"    Created: {formatted_batches}")
        formatted_batches_rolled_back = format_total(
            totals["batches"]["created_but_rolled_back"], totals["batches"]["processed"]
        )
        print(f"    Created but rolled back: {formatted_batches_rolled_back}")

        print("  Cases:")
        formatted_cases = format_total(
            totals["cases"]["created"], totals["cases"]["processed"]
        )
        print(f"    Created: {formatted_cases}")
        formatted_cases_rolled_back = format_total(
            totals["cases"]["created_but_rolled_back"], totals["cases"]["processed"]
        )
        print(f"    Created but rolled back: {formatted_cases_rolled_back}")

        cases_with_errors = (
            totals["cases"]["processed"]
            - totals["cases"]["created_but_rolled_back"]
            - totals["cases"]["created"]
        )
        formatted_cases_with_errors = format_total(
            cases_with_errors, totals["cases"]["processed"]
        )
        print(f"    Errors: {formatted_cases_with_errors}")

        print("  Facilities:")
        formatted_facilities = format_total(
            totals["facilities"]["created"], totals["facilities"]["processed"]
        )
        print(f"    Created: {formatted_facilities}")

        # formatted_batches_no_errors = format_total(
        #     totals["batches"]["created_no_errors"], totals["batches"]["processed"]
        # )
        # print(f"    with NO errors: {formatted_batches_no_errors}")

        formatted_facilities_rolled_back = format_total(
            totals["facilities"]["created_but_rolled_back"],
            totals["facilities"]["processed"],
        )
        print(f"    Created but rolled back: {formatted_facilities_rolled_back}")

        facilities_with_errors = (
            totals["facilities"]["processed"]
            - totals["facilities"]["created_but_rolled_back"]
            - totals["facilities"]["created"]
        )
        formatted_facilities_with_errors = format_total(
            facilities_with_errors, totals["facilities"]["processed"]
        )
        print(f"    Errors: {formatted_facilities_with_errors}")
        # print(
        #     f"  Successfully created {total_batches_created}/{total_files_processed} Batches, "
        #     f"{total_cases_created}/{total_cases_processed} Cases, "
        #     f"and {total_facilities_created}/{total_facilities_processed} Facilities:"
        # )

    def process(self):
        totals = {
            "batches": {
                "created": 0,
                "created_but_rolled_back": 0,
                "created_no_errors": 0,
                "processed": 0,
            },
            "cases": {"created": 0, "created_but_rolled_back": 0, "processed": 0},
            "facilities": {"created": 0, "created_but_rolled_back": 0, "processed": 0},
        }
        report_summary = {}
        for importer in self.excel_collection_importer.excel_importers:
            import_reporter = importer.report
            if importer.rolled_back:
                creation_key = "created_but_rolled_back"
            else:
                creation_key = "created"
            totals["batches"]["processed"] += 1
            # if not import_reporter.has_errors():
            #     totals["batches"]["created_no_errors"] += 1
            # if not import_reporter.has_fatal_errors():
            totals["batches"][creation_key] += 1

            for error_category, errors_by_type in import_reporter.report.items():
                if error_category not in ["batch_errors", "sheet_errors"]:
                    continue
                if error_category not in report_summary:
                    report_summary[error_category] = {}
                for error_type, errors_ in errors_by_type.items():

                    if error_type in report_summary[error_category]:
                        report_summary[error_category][error_type].update(errors_)
                    else:
                        report_summary[error_category][error_type] = set(errors_)

            totals["cases"]["processed"] += import_reporter.cases_processed
            totals["facilities"]["processed"] += import_reporter.facilities_processed

            totals["cases"][creation_key] += len(import_reporter.cases_created)
            totals["facilities"][creation_key] += len(
                import_reporter.facilities_created
            )

        print("-" * 80)
        self.print_summary(report_summary)

        print("-" * 80)
        self.print_report()

        print("-" * 80)
        # self.print_totals(totals)


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
        self.fatal_error_ocurred = False

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
        if (
            "sheet_errors" in self.report
            and "unmapped_headers" in self.report["sheet_errors"]
        ):
            error_summary["Unmapped Headers"] = self.report["sheet_errors"][
                "unmapped_headers"
            ]

        column_error_summary = {}
        if "row_errors" in self.report:
            for error_type, errors in self.report["row_errors"].items():
                for error in errors:
                    if "field" not in error:
                        import ipdb

                        ipdb.set_trace()
                    field = error["field"]
                    if field in column_error_summary:
                        column_error_summary[field].append(error["row"])
                    else:
                        column_error_summary[field] = [error["row"]]

        #                 if field in column_error_summary:
        #                     if (
        #                         row_error["value"]
        #                         not in column_error_summary[field]["Invalid Values"]
        #                     ):
        #                         column_error_summary[field]["Invalid Values"].append(
        #                             str(row_error["value"])
        #                         )
        #                 else:
        #                     column_error_summary[field] = OrderedDict(
        #                         (
        #                             ("Field", field),
        #                             ("Invalid Values", [str(row_error["value"])]),
        #                         )
        #                     )
        if column_error_summary:
            # error_summary["Column Errors"] = sorted(
            #     column_error_summary.values(), key=lambda x: x["Field"]
            # )

            error_summary["by_field"] = column_error_summary

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
        if self.fatal_error_ocurred:
            return True
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
    # TODO: Probably not needed here...
