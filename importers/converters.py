"""Library of field converters

These are responsible for taking a field value from an external
source and converting/validating it in some way in order to
make it compatible with a database field
"""

from datetime import datetime, date
import re

import pytz

from django.contrib.gis.db.backends.postgis.models import PostGISSpatialRefSys
from django.contrib.gis.geos import Point

from utils.coord_utils import dms_to_dd
from utils.constants import NAD27_SRID, NAD83_SRID
from .constants import MIN_VALID_CASE_NUMBER, MAX_VALID_CASE_NUMBER

ARRAY_DELIMITER_REGEX = re.compile("[,/]")

FEET_IN_A_METER = 0.3048

# https://regex101.com/r/4DTp5D/4
SCI_REGEX_STR = r"(?P<digits>\d+(?:\.\d*)?)(?:(?:x\d+[0]\^?)|x?1?e)(?P<exponent>\-?\d+)"
SCI_REGEX = re.compile(SCI_REGEX_STR, re.IGNORECASE)

COORD_PATTERN_STR = (
    r"(?P<degrees>-?\d+)(?:\s+|-)(?P<minutes>\d+)(?:\s+|-)(?P<seconds>\d+(?:\.\d+)?)"
)
COORD_PATTERN = re.compile(COORD_PATTERN_STR)

CASE_REGEX_STR = r"^P?(?P<case_num>\d+).*"
CASE_REGEX = re.compile(CASE_REGEX_STR)
MDY_REGEX = re.compile(r"(?P<month>\d{1,2})[/\\](?P<day>\d{1,2})[/\\](?P<year>\d{1,4})")

# TODO:
# https://regex101.com/r/gRPTN8/5
# nrqz_id_regex_str = r"^(?P<case_num>\d+)(?:[\-\_](?:REV
# )?(?P<site_num>\d+))?(?:[\s_\*]+(?:\(.*\)[\s_]+)?(?P<site_name>(?:(?:\w+\s+)?\S{5}|\D+))[\s_]+(?P<facility_name>\S+))?"
# nrqz_id_regex = re.compile(nrqz_id_regex_str)
def convert_nrqz_id_to_case_num(nrqz_id):
    match = CASE_REGEX.match(str(nrqz_id))
    if not match:
        raise ValueError(
            f"Could not parse NRQZ ID '{nrqz_id}' using '{CASE_REGEX_STR}'!"
        )
    return convert_case_num(match["case_num"])


def coerce_feet_to_meters(value):
    feet = coerce_positive_float(value)
    if feet is None:
        return feet
    return feet * FEET_IN_A_METER


def coerce_scientific_notation(value):
    # First, assume that it _isn't_ scientific notation,
    # and is instead a simple float (this does happen)
    try:
        return float(value)
    except ValueError:
        pass

    # If that doesn't work, we'll try to convert it from
    # scientific notation
    clean_value = "".join(value.split())
    clean_value = coerce_none(clean_value)
    if not clean_value:
        return None
    match = SCI_REGEX.search(clean_value)
    if match:
        digits = match.groupdict()["digits"]
        exponent = match.groupdict()["exponent"]
    else:
        raise ValueError(
            f"Failed to parse {value!r} (clean: {clean_value!r} with regex {SCI_REGEX_STR}"
        )

    try:
        float(digits) * 10 ** float(exponent)
    except ValueError:
        import ipdb

        ipdb.set_trace()


def coerce_none(value, none_str_values=("", "None", "#N/A", "Not provided")):
    clean = str(value).strip().lower()
    if clean in [v.lower() for v in none_str_values]:
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


def convert_mdy_datetime(value):
    # Strip all whitespace
    clean_value = "".join(str(value).split())
    m = MDY_REGEX.search(clean_value)
    if not m:
        raise ValueError(
            f"Could not match MDY date {value!r} with regex {MDY_REGEX.pattern}"
        )

    return date(int(m["year"]), int(m["month"]), int(m["day"]))


def convert_access_datetime(value):
    if value == "":
        return None
    date_str = value.split(" ")[0]
    month, day, year = date_str.split("/")
    return datetime(int(year), int(month), int(day), tzinfo=pytz.utc)


def coerce_positive_int(value):
    num = coerce_float(value)
    if num is None or num < 1:
        return None

    return int(num)


def coerce_positive_float(value):
    num = coerce_float(value)
    if num is None or num < 1:
        return None

    return float(num)


def convert_case_num(value):
    case_num = coerce_positive_int(value)
    if case_num is None:
        return case_num

    if case_num > MAX_VALID_CASE_NUMBER:
        raise ValueError(
            f"Case number {case_num} is larger than maximum "
            f"acceptable value {MAX_VALID_CASE_NUMBER}"
        )

    elif case_num < MIN_VALID_CASE_NUMBER:
        raise ValueError(
            f"Case number {case_num} is smaller than minimum "
            f"acceptable value {MIN_VALID_CASE_NUMBER}"
        )

    return case_num


def coerce_bool(value):
    """Coerce a string to a bool, or to None"""

    clean_value = str(value).strip().lower()
    if clean_value in ["yes", "1", "true", "t"]:
        return True
    elif clean_value in ["no", "n0", "0", "false", "f"]:
        return False
    elif clean_value in ["", "na", "n/a", "none"]:
        return None
    else:
        raise ValueError("Could not determine truthiness of value {!r}".format(value))


def coerce_str(value):
    clean_value = str(value).strip().lower()
    if clean_value in ["", "na", "n/a", "#n/a", "'#n/a'"]:
        return None
    else:
        return value


def coerce_float(value):
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
        clean_value = re.sub(r"[^0-9\.]", "", clean_value)

    # If the string is empty after stripping non-decimal characters out,
    # treat it as None
    if clean_value == "":
        return None

    return float(clean_value)


def coerce_coords(value):
    """Given a coordinate in DD MM SS.sss format, return it in DD.ddd format"""
    clean_value = str(value).strip().lower()

    if clean_value in ["", "none", "#n/a", "none provided"]:
        return None

    try:
        dd = float(value)
    except ValueError:
        match = re.match(COORD_PATTERN, clean_value)
        if not match:
            raise ValueError(f"Regex {COORD_PATTERN_STR} did not match value {value!r}")

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


def coerce_location_(latitude, longitude, srid=NAD83_SRID):
    converted_latitude = coerce_lat(latitude)
    converted_longitude = coerce_long(longitude)
    if not converted_latitude or not converted_longitude:
        # tqdm.write(f"Null coordinates given: ({latitude!r}, {longitude!r})")
        return None

    if converted_longitude > 0:
        converted_longitude *= -1
    point = Point(x=converted_longitude, y=converted_latitude, srid=srid)
    return point


# NRQZ LOCS!
# Note that these are NOT both required, because location is not a required field
def coerce_location(latitude=None, longitude=None, srid=NAD83_SRID):
    point = coerce_location_(latitude, longitude, srid)
    if point is None:
        return point
    converted_longitude, converted_latitude = point.x, point.y

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

    return point


def convert_freq_high(freq_low=None, freq_high=None):
    if freq_high is None:
        return None

    freq_high = coerce_positive_float(freq_high)
    if freq_high is None:
        return None

    freq_low = coerce_positive_float(freq_low)
    if freq_low is not None:
        if freq_high < freq_low:
            raise ValueError(f"freq_high {freq_high} is lower than freq_low {freq_low}")

    return freq_high


def convert_access_path(path):
    if not path:
        return None

    return path.split("#")[1].strip()


def convert_access_attachment(**kwargs):
    if len(kwargs) != 1:
        raise TypeError(
            f"convert_access_attachment handles only a single kwarg! Got: {kwargs}"
        )

    letter_name, path = next(iter(kwargs.items()))
    # Save some time; no sense doing anything if the path is None. We don't
    # want to even create an Attachment in this case
    if not path:
        return None
    # Pull out the actual path value from the
    clean_path = convert_access_path(path)
    # Strip all non-number characters, leaving only the number
    letter_number = re.sub("[^0-9]", "", letter_name)

    return {"path": clean_path, "original_index": letter_number}


def coerce_access_location(latitude, longitude, nad27=None, nad83=None):
    if nad27 is nad83 is True:
        raise ValueError(
            "Both NAD27 and NAD83 are indicated as True; this must be resolved!"
        )

    if nad27:
        srid = NAD27_SRID
    else:
        srid = NAD83_SRID
    return {
        "location": coerce_location(latitude, longitude, srid=srid),
        "original_srs": PostGISSpatialRefSys.objects.get(srid=srid).pk,
    }


def convert_array(**kwargs):
    values = tuple(
        v.strip().upper()
        for value in kwargs.values()
        for v in ARRAY_DELIMITER_REGEX.split(value)
        if v.strip()
    )
    if not values:
        return None
    return ",".join(values)


def convert_case_num_and_site_num_to_nrqz_id(case_num, site_num=None):
    case_num = convert_nrqz_id_to_case_num(case_num)
    if site_num:
        return f"{case_num}-{site_num}"
    return f"{case_num}"


def convert_empty_string(string_):
    # print(string_)
    if string_ is None:
        return ""
    return string_
