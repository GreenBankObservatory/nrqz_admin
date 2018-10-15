import json
from collections import namedtuple, OrderedDict
from pprint import pprint

class ErrorReporter:
    def __init__(self, filename):
        self.filename = filename

        self.report = {
            "sheet_errors": [],
            "unmapped_headers": [],
            "data_errors": {},
        }

    def add_sheet_error(self, error):
        self.report["sheet_errors"].append(error)

    def add_unmapped_header(self, header):
        self.report["unmapped_headers"].append(header)

    def add_row_error(self, header, row_num, error):
        if header not in self.report["data_errors"]:
            self.report["data_errors"][header] = {}

        self.report["data_errors"][header][row_num] = error

    def print_report(self):
        print("Sheet Errors:")
        for error in self.report["sheet_errors"]:
            print(error)

        print("Unmapped headers:")
        for header in self.report["unmapped_headers"]:
            print(f"  {header!r}")

        print("Data Errors:")
        for header, errors_by_row in self.report["data_errors"].items():
            print(f"  {header}:")
            for row_num, error in errors_by_row.items():
                print(f"    {row_num}:")

                for key, value in error.items():
                    print(f"      {key}: {value!r}")

        # print(json.dumps(self.report, indent=2))
        pass



    def generate_error_summary(self):
        """Generate a more concise error report"""

        error_summary = {}
        error_summary["sheet_errors"] = self.report["sheet_errors"]
        error_summary["unmapped_headers"] = self.report["unmapped_headers"]




        column_error_summary = {}
        for header, errors_by_row in self.report["data_errors"].items():
            for row_num, header_error in errors_by_row.items():
                if header in column_error_summary:
                    if (
                        header_error["value"]
                        not in column_error_summary[header]["Invalid Values"]
                    ):
                        column_error_summary[header]["Invalid Values"].append(
                            str(header_error["value"])
                        )
                else:
                    column_error_summary[header] = OrderedDict(
                        (
                            ("Header", header),
                            ("Converter", header_error["converter"]),
                            ("Invalid Values", [str(header_error["value"])]),
                        )
                    )
        if column_error_summary:
            error_summary["Column Errors"] = sorted(
                column_error_summary.values(), key=lambda x: x["Header"]
            )

        return error_summary
