"""Library of field converters

These are responsible for taking a field value from an external
source and converting/validating it in some way in order to
make it compatible with a database field
"""

import re

from utils.coord_utils import dms_to_dd

FEET_IN_A_METER = 0.3048

SCI_REGEX_STR = r"(?P<digits>\d+.?\d*)(?:(?:X10\^)|(?:E))(?P<exponent>\-?\d+)"
SCI_REGEX = re.compile(SCI_REGEX_STR, re.IGNORECASE)


def coerce_feet_to_meters(value):
    if value in [None, ""]:
        return value

    feet = float(value)
    return feet * FEET_IN_A_METER


def coerce_scientific_notation(value):
    if not value.strip():
        return None
    match = SCI_REGEX.search(value)
    if match:
        digits = match.groupdict()["digits"]
        exponent = match.groupdict()["exponent"]
    else:
        raise ValueError(f"Failed to parse {value} with regex {SCI_REGEX_STR}")

    return float(digits) * 10 ** float(exponent)


def coerce_none(value):
    clean = value.strip().lower()
    if clean in ["", "None"]:
        return None
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
