from tqdm import tqdm

from django_import_data import BaseImportCommand

from importers.handlers import handle_case, handle_attachments
from importers.nrqz_analyzer.fieldmap import (
    APPLICANT_FORM_MAP,
    CONTACT_FORM_MAP,
    CASE_FORM_MAP,
    FACILITY_FORM_MAP,
    STRUCTURE_FORM_MAP,
)


class Command(BaseImportCommand):
    help = "Import NRQZ Application Maker Data"

    PROGRESS_TYPE = BaseImportCommand.PROGRESS_TYPES.FILE
    FORM_MAPS = [
        APPLICANT_FORM_MAP,
        CONTACT_FORM_MAP,
        CASE_FORM_MAP,
        FACILITY_FORM_MAP,
        STRUCTURE_FORM_MAP,
    ]

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
                                # tqdm.write(f"END DICT")
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
                        # tqdm.write(f"START DICT")
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
        return main_dict, facility_dicts, errors

    def handle_v1_format(self, data):
        return self.deconstruct_data(data, facility_dict_terminator="ga2gbt")

    def handle_v2_format(self, data):
        return self.deconstruct_data(data, facility_dict_terminator="PanRng")

    def handle_record(self, row_data, file_import_attempt):
        version = row_data.data[0].strip()
        if version == "nrqzApp v1":
            # tqdm.write("Handling v1")
            main_dict, facility_dicts, errors = self.handle_v1_format(row_data.data)
        elif version == "nrqzApp v2":
            # tqdm.write("Handling v2")
            main_dict, facility_dicts, errors = self.handle_v2_format(row_data.data)
        else:
            raise ValueError(f"Unknown version: {version}")

        if errors:
            file_import_attempt.errors.update(errors)
            file_import_attempt.save()
        applicant, applicant_audit = APPLICANT_FORM_MAP.save_with_audit(
            row_data=row_data, data=main_dict, file_import_attempt=file_import_attempt
        )
        contact, contact_audit = CONTACT_FORM_MAP.save_with_audit(
            row_data=row_data, data=main_dict, file_import_attempt=file_import_attempt
        )
        case, case_created = handle_case(
            row_data,
            CASE_FORM_MAP,
            data=main_dict,
            applicant=applicant,
            contact=contact,
            file_import_attempt=file_import_attempt,
        )

        structure, structure_audit = STRUCTURE_FORM_MAP.save_with_audit(
            row_data, data=main_dict, file_import_attempt=file_import_attempt
        )

        for facility_dict in facility_dicts:
            facility, facility_audit = FACILITY_FORM_MAP.save_with_audit(
                row_data,
                data=facility_dict,
                extra={
                    "case": case.id if case else None,
                    "structure": structure.id if structure else None,
                },
                file_import_attempt=file_import_attempt,
            )

        headers = set(main_dict)
        for facility_keys in facility_dicts:
            headers.update(facility_keys)

        info, errors = self.header_checks(headers)
        file_import_attempt.info = info
        file_import_attempt.errors = errors
        file_import_attempt.save()

    def file_level_checks(self, rows):
        return {}, {}

    # def post_import_checks(self, file_import_attempts):
    #     if len(file_import_attempts) != 1:
    #         raise ValueError("There should only be one FIA!")

    #     file_import_attempt = file_import_attempts[0]
