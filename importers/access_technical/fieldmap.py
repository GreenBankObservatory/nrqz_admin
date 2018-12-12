"""Field mappings for Access Technical Data"""

import re

from importers.fieldmap import FieldMap
from importers.access_application.fieldmap import coerce_datetime, coerce_positive_int
from utils.coord_utils import dms_to_dd

sci_regex_str = r"(?P<digits>\d+.?\d*)(?:(?:X10\^)|(?:E))(?P<exponent>\-?\d+)"
sci_regex = re.compile(sci_regex_str, re.IGNORECASE)

FEET_IN_A_METER = 0.3048


def coerce_feet_to_meters(value):
    if value in [None, ""]:
        return value

    feet = float(value)
    return feet * FEET_IN_A_METER


def coerce_scientific_notation(value):
    if not value.strip():
        return None
    m = sci_regex.search(value)
    if m:
        digits = m.groupdict()["digits"]
        exponent = m.groupdict()["exponent"]
    else:
        raise ValueError(f"Failed to parse {value} with regex {sci_regex_str}")

    return float(digits) * 10 ** float(exponent)


def coerce_none(value):
    clean = value.strip().lower()
    if clean in ["", "None"]:
        return None
    else:
        return value


def coerce_coords(value):
    clean = value.strip()
    if clean in ["", "None"]:
        return None

    if "." in clean:
        number, remain = clean.split(".")
    else:
        number = clean
        remain = None

    if number.startswith("-"):
        negative = True
        number = number[1:]
    else:
        negative = False

    # Yes, I agree that this is incredibly stupid. But so is
    # storing coordinates as D,M,S in a float field
    if len(number) == 7:
        decimal = number[:3]
        minutes = number[3:5]
        seconds = number[5:8]
    elif len(number) == 6:
        decimal = number[:2]
        minutes = number[2:4]
        seconds = number[4:7]
    elif len(number) == 5:
        decimal = number[:2]
        minutes = number[2:4]
        seconds = number[4:6]
    elif len(number) == 4:
        decimal = number[:2]
        minutes = number[2:4]
        seconds = 0
    elif len(number) == 2:
        decimal = number[:2]
        minutes = 0
        seconds = 0
    else:
        raise ValueError(f"Invalid coords ({value!r}); {len(number)}")

    if negative:
        decimal = "-" + decimal
    if remain:
        seconds = f"{seconds}.{remain}"
    # print(f"Parsed {value} into {decimal}, {minutes}, {seconds}")
    return dms_to_dd(decimal, minutes, seconds)


applicant_field_mappers = [
    FieldMap(to_field="name", converter=None, from_field="APPLICANT")
]

facility_field_mappers = [
    FieldMap(to_field="case_num", converter=coerce_positive_int, from_field="NRQZ_NO"),
    FieldMap(to_field="antenna_model_number", converter=None, from_field="ANT_MODEL"),
    FieldMap(
        to_field="original_created_on", converter=coerce_datetime, from_field="DATEREC"
    ),
    FieldMap(to_field="call_sign", converter=None, from_field="CALLSIGN"),
    FieldMap(to_field="freq_low", converter=None, from_field="FREQUENCY"),
    FieldMap(
        to_field="power_density_limit",
        converter=coerce_scientific_notation,
        from_field="PWD_LIMIT",
    ),
    FieldMap(to_field="site_num", converter=coerce_positive_int, from_field="SITE."),
    # TODO: hmmmm
    FieldMap(to_field="site_name", converter=None, from_field="LOCATION"),
    FieldMap(to_field="latitude", converter=coerce_none, from_field="LATITUDE"),
    FieldMap(to_field="longitude", converter=coerce_none, from_field="LONGITUDE"),
    FieldMap(to_field="amsl", converter=coerce_feet_to_meters, from_field="GND_ELEV"),
    FieldMap(to_field="agl", converter=coerce_feet_to_meters, from_field="ANT_HEIGHT"),
    FieldMap(to_field="comments", converter=None, from_field="REMARKS"),
]


def expand_field_mappers(field_mappers):
    """Generate a map of known_header->importer by "expanding" the from_fields of each FieldMap
    In this way we can easily and efficiently look up a given header and find its associated importer
    """

    field_map = {}
    for importer in field_mappers:
        field_map[importer.from_field] = importer

    return field_map


def get_combined_field_map():
    return expand_field_mappers([*applicant_field_mappers, *facility_field_mappers])


def print_field_map(field_map):
    """Print out a simple report of the final header->field mappings"""

    # from_field_len is just the longest header in the map plus some padding
    from_field_len = max(len(from_field) for from_field in field_map) + 3
    for from_field, importer in field_map.items():
        print(f"{from_field!r:{from_field_len}}: {importer.to_field!r}")


if __name__ == "__main__":
    print("Case field map:")
    print_field_map(expand_field_mappers(facility_field_mappers))
    print()
    print("Person field map:")
    print_field_map(expand_field_mappers(person_field_mappers))
