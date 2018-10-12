"""Provides utilities for mapping header->field

The problem: we have a bunch of Excel files, e.g., that have columnar data we
wish to create model instances from. Each column should map to a field, but
the columns don't always have the same names between Excel files. So, we need
some way to map all possible column headers to their appropriate field.

Additionally, we need a way to link a "converter" to each pairing -- this is
responsible for cleaning the data and converting it to the proper type. For
example, if we have a boolean column that represents None as either "" or "n/a",
depending on the file, we need a way to say that all of those mean the same thing.

This module contains all of the converters and the FieldMap class itself,
as well as an dictionary of every known header to its mapped field -- "expanded"
from the list of FieldMap instances
"""

import re
import string

from utils.coord_utils import dms_to_dd


COORD_PATTERN_STR = r"^(?P<degrees>\d+)\s+(?P<minutes>\d+)\s+(?P<seconds>\d+(?:\.\d+)?)$"
COORD_PATTERN = re.compile(COORD_PATTERN_STR)


def coerce_bool(value):
    """Coerce a string to a bool, or to None"""

    clean_value = str(value).strip().lower()
    if clean_value.startswith("yes"):
        return True
    elif clean_value.startswith("no"):
        return False
    elif clean_value in ["", "na", "n/a"]:
        return None
    else:
        raise ValueError("Could not determine truthiness of value {!r}".format(value))


def coerce_num(value):
    """Coerce a string to a number, or to None"""

    clean_value = str(value).strip().lower()
    if clean_value in ["", "na", "n/a", "no"]:
        return None


    if clean_value == "quad":
        clean_value = 4
    elif clean_value == "hex":
        clean_value = 6
    elif clean_value == "deca":
        clean_value = 10
    else:
        clean_value = re.sub(f"[{string.ascii_letters}]", '', clean_value)

    return float(clean_value)


def cooerce_coords(value):
    """Given a coordinate in DD MM SS.sss format, return it in DD.ddd format"""
    clean_value = str(value).strip().lower()

    if clean_value in ["", "None"]:
        return None

    match = re.match(COORD_PATTERN, clean_value)
    if not match:
        raise ValueError(f"Regex {COORD_PATTERN_STR} did not match value {value}")

    dd = dms_to_dd(**match.groupdict())
    return dd

def cooerce_lat(value):
    return cooerce_coords(value)

def cooerce_long(value):
    # Need to invert this because all of our longitudes will be W
    return -1 * cooerce_coords(value)

class FieldMap:
    """Map field to its associated headers and to a converter"""

    def __init__(self, to_field, converter, from_fields=None, from_field=None):
        # Headers the to_field could potentially be associated with
        self.to_field = to_field
        # Function to convert/clean data
        self.converter = converter if converter else self.nop_converter
        if from_fields and from_field:
            raise ValueError("Cannot provide both from_fields and from_field")
        elif not (from_fields or from_field):
            raise ValueError("Must provide exactly one of from_fields or from_field")

        self.from_field = from_field
        self.from_fields = from_fields

    @staticmethod
    def nop_converter(value):
        """Perform no conversion; simply return value"""
        return value

    def __repr__(self):
        return f"{self.to_field} <{self.converter.__name__}>: {self.from_fields}"
