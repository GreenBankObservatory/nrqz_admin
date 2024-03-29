"""Import NRQZ Analyzer Data"""

import re

from django_import_data import BaseImportCommand

from importers.handlers import handle_case
from importers.nrqz_analyzer.formmaps import (
    CASE_FORM_MAP,
    FACILITY_FORM_MAP,
    IGNORED_HEADERS,
)

COMMENT_REGEX = re.compile(r"\d{2}\s*[a-zA-Z]{3,6}\s*\d{2,4}")


class Command(BaseImportCommand):
    help = "Import NRQZ Application Maker Data"

    PROGRESS_TYPE = BaseImportCommand.PROGRESS_TYPES.FILE
    FORM_MAPS = [CASE_FORM_MAP, FACILITY_FORM_MAP]

    IGNORED_HEADERS = IGNORED_HEADERS

    MODELS_TO_REIMPORT = ["facility"]

    def load_rows(self, path):
        with open(path, newline="", encoding="latin1") as file:
            lines = file.readlines()

        return [lines]

    def deconstruct_data(self, data, facility_dict_terminator):
        # Strip off the version line
        lines = data[1:]
        # lines = row.split("\n")
        # The "main" dict holds all of the non-facility info
        main_dict = {}
        # The Facility dicts holds a facility dict for each facility in
        # the facility table
        facility_dicts = []
        facility_dict = None
        errors = {}
        for line in lines:
            stripped = line.strip()
            if stripped:
                parts = [part for part in stripped.split(":") if part]
                key = parts[0]
                value = ":".join(parts[1:])

                if ":" not in stripped:
                    errors.setdefault("non_key_value_rows", [])
                    errors["non_key_value_rows"].append(stripped)
                    main_dict.setdefault("comments", "")
                    main_dict["comments"] += line

                # If we are "in" a Facility dict...
                if facility_dict:
                    # ...put the current key/value pair into it
                    if key not in facility_dict:
                        if value:
                            facility_dict[key] = value
                        # ga2gbt marks the end of a "facility run". So, once we reach
                        # that we add the facility dict to our list thereof and
                        # null out the facility_dict so the cycle can continue
                        if key == facility_dict_terminator:
                            if facility_dict:
                                facility_dicts.append(facility_dict)
                            facility_dict = None
                    # Unless it is already there, which should never happen
                    else:
                        raise ValueError(
                            f"Key {key} found more than once in a single Facility dict!"
                        )

                # If we are NOT in a Facility dict...
                else:
                    # type marks the beginning of a "facility run"
                    if key == "type":
                        # So, we start a new dict to hold its info. Note that we
                        # add both the "type" here, AND the nrqzID. This is so
                        # that each Facility knows what its nrqzID and case number are
                        facility_dict = {
                            key: value
                            for key, value in main_dict.items()
                            if key in ["nrqzID", "lat", "lon"]
                        }
                        if value:
                            if value not in facility_dict:
                                facility_dict["type"] = value
                            else:
                                raise ValueError("fajsdfsad")
                    # For all other keys, simply add them to the main dict
                    else:
                        if value:
                            # Last value wins...
                            main_dict[key] = value
                            # if key not in main_dict:
                            #     main_dict[key] = value
                            # else:
                            #     raise ValueError(
                            #         f"Key {key} found more than once in the 'main' dict!"
                            #     )

                            m = COMMENT_REGEX.match(line)
                            if m:
                                main_dict.setdefault("comments", "")
                                main_dict["comments"] += line
        return main_dict, facility_dicts, errors

    def handle_v1_format(self, data):
        return self.deconstruct_data(data, facility_dict_terminator="ga2gbt")

    def handle_v2_format(self, data):
        return self.deconstruct_data(data, facility_dict_terminator="PanRng")

    def derive_keys(self, data):
        keys = set()
        for line in data:
            stripped = line.strip()
            if stripped:
                parts = [part for part in stripped.split(":") if part]
                key = parts[0]
                keys.add(key)

        return sorted(keys)

    def handle_record(self, row_data, durable=True):
        version = row_data.data[0].strip()
        if version == "nrqzApp v1":
            main_dict, facility_dicts, errors = self.handle_v1_format(row_data.data)
        elif version == "nrqzApp v2":
            main_dict, facility_dicts, errors = self.handle_v2_format(row_data.data)
        else:
            raise ValueError(f"Unknown version: {version}")

        if errors:
            row_data.file_import_attempt.errors.update(errors)
            row_data.file_import_attempt.save()

        original_headers = self.derive_keys(row_data.data)
        row_data.headers = original_headers
        fixed_row_data = {"main_dict": main_dict, "facility_dicts": facility_dicts}
        row_data.data = fixed_row_data
        row_data.save()
        case, case_created = handle_case(
            row_data, CASE_FORM_MAP, data=main_dict, imported_by=self.__module__
        )

        if case_created:
            error_str = "Case should never be created from technical data; only found!"
            if durable:
                row_data.errors.setdefault("case_not_found_errors", [])
                row_data.errors["case_not_found_errors"].append(error_str)
                row_data.save()
            else:
                raise ValueError(error_str)

        for facility_dict in facility_dicts:
            facility, facility_audit = FACILITY_FORM_MAP.save_with_audit(
                row_data,
                data=facility_dict,
                extra={"case": case.case_num if case else None},
                imported_by=self.__module__,
            )

        headers = set(main_dict)
        for facility_keys in facility_dicts:
            headers.update(facility_keys)

        info, errors = self.header_checks(headers)
        row_data.file_import_attempt.info = info
        row_data.file_import_attempt.errors = errors
        row_data.file_import_attempt.save()

    def file_level_checks(self, rows):
        return {}, {}
