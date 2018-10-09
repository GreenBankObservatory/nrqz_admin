"""Provides utilities for mapping header->field

The problem: we have a bunch of Excel files, e.g., that have columnar data we
wish to create model instances from. Each column should map to a field, but
the columns don't always have the same names between Excel files. So, we need
some way to map all possible column headers to their appropriate field.

Additionally, we need a way to link a "converter" to each pairing -- this is
responsible for cleaning the data and converting it to the proper type. For
example, if we have a boolean column that represents None as either "" or "n/a",
depending on the file, we need a way to say that all of those mean the same thing.

This module contains all of the converters and the FieldImport class itself,
as well as an dictionary of every known header to its mapped field -- "expanded"
from the list of FieldImport instances
"""

# TODO: Make this module generic! Should not have code for import_excel_application

import re


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
    return value

def dms_to_dd(degrees, minutes, seconds):
    """Convert degrees, minutes, seconds to decimal degress"""

    dd = float(degrees) + float(minutes) / 60 + float(seconds) / 3600
    return dd

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

class FieldImport:
    def __init__(self, field, converter, known_headers):
        # Headers the field could potentially be associated with
        self.field = field
        # Function to convert/clean data
        self.converter = converter if converter else self.default_converter
        self.known_headers = known_headers

    @staticmethod
    def default_converter(value):
        return value

    def __repr__(self):
        return f"{self.field} <{self.converter.__name__}>: {self.known_headers}"


field_importers = [
    FieldImport(
        field="freq_low", converter=coerce_num, known_headers=["Freq Low (MHz)"]
    ),
    FieldImport(field="site_name", converter=None, known_headers=["Site Name"]),
    FieldImport(field="call_sign", converter=None, known_headers=["Call Sign"]),
    FieldImport(
        field="fcc_file_number", converter=None, known_headers=["FCC File Number"]
    ),
    FieldImport(field="latitude", converter=cooerce_coords, known_headers=["LAT (dd mm ss.ss)"]),
    FieldImport(
        field="longitude",
        converter=cooerce_coords,
        known_headers=["LON (-dd mm ss.ss)", "LON (dd mm ss.ss)"],
    ),
    FieldImport(field="amsl", converter=coerce_num, known_headers=["AMSL (m)"]),
    FieldImport(field="agl", converter=coerce_num, known_headers=["AGL (m)"]),
    FieldImport(
        field="freq_high", converter=coerce_num, known_headers=["Freq High (MHz)"]
    ),
    FieldImport(
        field="bandwidth",
        converter=coerce_num,
        known_headers=["Bandwidth (MHz)", "Minimum Bandwidth (MHz) utilized per TX"],
    ),
    FieldImport(
        field="max_output",
        converter=coerce_num,
        known_headers=["Max Tx Pwr (W)", "Max Output Pwr (W) Per TX"],
    ),
    FieldImport(
        field="antenna_gain", converter=coerce_num, known_headers=["Antenna Gain (dBi)"]
    ),
    FieldImport(
        field="system_loss", converter=coerce_num, known_headers=["System Loss (dB)"]
    ),
    FieldImport(
        field="main_beam_orientation",
        converter=None,
        known_headers=["Main Beam Orientation (All Sectors)"],
    ),
    FieldImport(
        field="mechanical_downtilt",
        converter=None,
        known_headers=["Mechanical Downtilt (All Sectors)"],
    ),
    FieldImport(
        field="electrical_downtilt",
        converter=None,
        known_headers=["Electrical Downtilt (All Sectors)"],
    ),
    FieldImport(
        field="antenna_model_number", converter=None, known_headers=["Antenna Model #"]
    ),
    FieldImport(
        field="nrqz_id",
        converter=None,
        known_headers=["NRQZ ID (to be assigned by NRAO)", "NRQZ ID"],
    ),
    FieldImport(
        field="tx_per_sector",
        converter=coerce_num,
        known_headers=[
            "Number of Transmitters per sector",
            "Total number of TXers (or No. of RRH's ports with feed power) per sector",
            "Number of TXers per sector",
        ],
    ),
    FieldImport(
        field="tx_antennas_per_sector",
        converter=coerce_num,
        known_headers=[
            "Number of TX antennas per sector",
            "Number of TX antennas per sector (Each polarization fed with TX power is considered an antenna).",
        ],
    ),
    FieldImport(
        field="technology",
        converter=None,
        known_headers=[
            "Technology 2G, 3G, 4G, other (specify)",
            "Technology i.e. FM, 2G, 3G, 4G, GSM, LTE, UMTS, CDMA2000 (specify other)",
        ],
    ),
    FieldImport(
        field="uses_split_sectorization",
        converter=coerce_bool,
        known_headers=[
            "This faciltiy uses Split sectorization (Yes or No)",
            "This faciltiy uses Split sectorization (or dual-beam sectorization) Indidate Yes or No",
        ],
    ),
    FieldImport(
        field="uses_cross_polarization",
        converter=coerce_bool,
        known_headers=[
            "This facility uses Cross polarization (Yes or No)",
            "This facility uses Cross polarization   Indicate Yes or No",
        ],
    ),
    FieldImport(
        field="quad_or_octal_polarization",
        converter=coerce_bool,
        known_headers=[
            "If this facility uses Quad or Octal polarization, specify type here"
        ],
    ),
    FieldImport(
        field="num_quad_or_octal_ports_with_feed_power",
        converter=coerce_num,
        known_headers=["Number of Quad or Octal ports with  feed power"],
    ),
    FieldImport(
        field="tx_power_pos_45",
        converter=coerce_num,
        known_headers=[
            'If YES to Col. "W", then what is the Max TX output PWR at +45 degrees'
        ],
    ),
    FieldImport(
        field="tx_power_neg_45",
        converter=coerce_num,
        known_headers=[
            'If YES to Col. "W", then what is the Max TX output PWR at -45 degrees'
        ],
    ),
    FieldImport(
        field="comments",
        converter=None,
        known_headers=["", "Additional information or comments from the applicant"],
    ),
    FieldImport(
        field="num_pols_with_feed_power", converter=coerce_num, known_headers=[]
    ),
]

# Generate a map of known_header->importer by "expanding" the known_headers of each FieldImporter
# In this way we can easily and efficiently look up a given header and find its associated importer
# NOTE: facility_field_map is the primary "export" of this module
facility_field_map = {}
for importer in field_importers:
    for header in importer.known_headers:
        facility_field_map[header] = importer


if __name__ == '__main__':
    # Print out a simple report of the final header->field mappings
    # header_len is just the longest header in the map plus some padding
    header_len = max(len(header) for header in facility_field_map) + 3
    for header, importer in facility_field_map.items():
        print(f"{header!r:{header_len}}: {importer.field!r}")
