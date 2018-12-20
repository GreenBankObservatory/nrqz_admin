"""Library of field converters

These are responsible for taking a field value from an external
source and converting/validating it in some way in order to
make it compatible with a database field
"""

from datetime import datetime
import re
import string

import pytz

from django.contrib.gis.geos import GEOSGeometry

from utils.coord_utils import dms_to_dd

FEET_IN_A_METER = 0.3048

SCI_REGEX_STR = r"(?P<digits>\d+.?\d*)(?:(?:X10\^)|(?:E))(?P<exponent>\-?\d+)"
SCI_REGEX = re.compile(SCI_REGEX_STR, re.IGNORECASE)

COORD_PATTERN_STR = (
    r"^(?P<degrees>\d+)\s+(?P<minutes>\d+)\s+(?P<seconds>\d+(?:\.\d+)?)$"
)
COORD_PATTERN = re.compile(COORD_PATTERN_STR)


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


def coerce_datetime(value):
    if value == "":
        return None
    date_str = value.split(" ")[0]
    month, day, year = date_str.split("/")
    return datetime(int(year), int(month), int(day), tzinfo=pytz.utc)


def coerce_positive_int(value):
    num = coerce_num(value)
    if num is None or num < 1:
        return None

    return int(num)


def coerce_path(value):
    if value == "":
        return None

    return value.split("#")[1]


def coerce_bool(value):
    """Coerce a string to a bool, or to None"""

    clean_value = str(value).strip().lower()
    if clean_value in ["yes", "1"]:
        return True
    elif clean_value in ["no", "n0", "0"]:
        return False
    elif clean_value in ["", "na", "n/a"]:
        return None
    else:
        raise ValueError("Could not determine truthiness of value {!r}".format(value))


def coerce_str(value):
    clean_value = str(value).strip().lower()
    if clean_value in ["", "na", "n/a", "#n/a"]:
        return None
    else:
        return value


def coerce_num(value):
    """Coerce a string to a number, or to None"""

    clean_value = str(value).strip().lower()
    if clean_value in ["", "na", "n/a", "no", "#n/a"]:
        return None

    if clean_value == "quad":
        clean_value = 4
    elif clean_value == "hex":
        clean_value = 6
    elif clean_value == "deca":
        clean_value = 10
    else:
        clean_value = re.sub(f"[{string.ascii_letters}]", "", clean_value)

    return float(clean_value)


def coerce_coords(value):
    """Given a coordinate in DD MM SS.sss format, return it in DD.ddd format"""
    clean_value = str(value).strip().lower()

    if clean_value in ["", "none", "#n/a"]:
        return None
    try:
        dd = float(value)
    except ValueError:
        match = re.match(COORD_PATTERN, clean_value)
        if not match:
            raise ValueError(f"Regex {COORD_PATTERN_STR} did not match value {value}")

        dd = dms_to_dd(**match.groupdict())
    return dd


def coerce_lat(value):
    return coerce_coords(value)


def coerce_long(value):
    # Need to invert this because all of our longitudes will be W
    longitude = coerce_coords(value)
    if longitude is not None:
        return -1 * longitude
    else:
        return None


def coerce_location(latitude, longitude):
    latitude = coerce_lat(latitude)
    longitude = coerce_long(longitude)
    return GEOSGeometry(f"Point({longitude} {latitude})")
