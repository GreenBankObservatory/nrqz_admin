"""Library of field converters

These are responsible for taking a field value from an external
source and converting/validating it in some way in order to
make it compatible with a database field
"""

from datetime import datetime
import re
import string

import pytz
from tqdm import tqdm

from django.contrib.gis.geos import GEOSGeometry, GEOSException

from utils.coord_utils import dms_to_dd

FEET_IN_A_METER = 0.3048

# https://regex101.com/r/4DTp5D/1
SCI_REGEX_STR = (
    r"(?P<digits>\d+.?\d*)\s*(?:(?:x\s*1[0-]\s*\^?)|(?:e))\s*(?P<exponent>\-?\d+)"
)
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


def coerce_none(value, none_str_values=("", "None")):
    clean = value.strip().lower()
    if clean in none_str_values:
        return None
    return value


def coerce_coord_from_number(value):
    # Strip whitespace from both sides
    clean = value.strip()
    # Strip any leading zeroes
    clean = value.lstrip("0")
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
        decimal = number[:2]
        minutes = number[2:4]
        seconds = number[4:]
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
    # tqdm.write(f"Parsed {value} into {decimal}, {minutes}, {seconds}")
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

    return value.split("#")[1].strip()


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
    else:
        dd = coerce_coord_from_number(clean_value)

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


def coerce_location_(latitude, longitude):
    converted_latitude = coerce_lat(latitude)
    converted_longitude = coerce_long(longitude)
    # tqdm.write(f"Converted latitude from {latitude} to {converted_latitude}")
    # tqdm.write(f"Converted longitude from {longitude} to {converted_longitude}")
    if converted_latitude is None or converted_longitude is None:
        return None
        # raise ValueError(f"Invalid coordinates given: ({latitude!r}, {longitude!r})")
    point = GEOSGeometry(f"Point({converted_longitude} {converted_latitude})")
    # tqdm.write(f"Created point: {point.coords}")
    return point


# NRQZ LOCS!
def coerce_location(latitude, longitude):
    point = coerce_location_(latitude, longitude)
    if point is None:
        return point
    converted_longitude, converted_latitude = point.coords

    if converted_longitude > 0:
        converted_longitude *= -1
    lat_lower_bound = 34
    lat_upper_bound = 41
    long_lower_bound = -83
    long_upper_bound = -74
    bad_lat = not (lat_lower_bound < converted_latitude < lat_upper_bound)
    bad_long = not (long_lower_bound < converted_longitude < long_upper_bound)

    if bad_lat or bad_long:
        error_str = (
            f"Successfully converted ({latitude}, {longitude}) to "
            f"({converted_latitude:.2f}, {converted_longitude:.2f}), but "
        )
        if bad_lat:
            error_str += (
                f"latitude ({converted_latitude:.2f}) is outside of acceptable bounds: "
                f"[{lat_lower_bound}, {lat_upper_bound}] "
            )
        if bad_long:
            error_str += (
                f"longitude ({converted_longitude:.2f}) is outside of acceptable bounds: "
                f"[{long_lower_bound}, {long_upper_bound}] "
            )

        raise ValueError(error_str)
