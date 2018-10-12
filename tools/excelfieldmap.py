import re

from tools.fieldmap import FieldMap, coerce_num, cooerce_lat, cooerce_long, coerce_bool

site_name_regex_str = r"(?P<nrqz_id>\d+)\s+(?P<site_name>\D+)\s+(?P<facility_name>\d+\S+)"
site_name_regex = re.compile()

def parse_site_name(value):
    match = re.match(site_name_regex, value)
    if not match:
        raise ValueError(f"Could not parse {value} using regex {site_name_regex_str}")

    return match.groupdict()

def coerce_nrqz_id(value):
    return parse_site_name("nrqz_id")

def coerce_site_name(value):
    return parse_site_name("site_name")

def coerce_facility_name(value):
    return parse_site_name("facility_name")

# TODO: FieldMap must be able to map a single header to multiple fields. Need to have
# a FieldMaps class (or similar) that holds a list of FieldMaps as well as:
# * a class (e.g. Facility) that will be created
# * ???
field_mappers = [
    FieldMap(to_field="freq_low", converter=coerce_num, from_fields=["Freq Low (MHz)"]),
    FieldMap(to_field="site_name", converter=None, from_fields=["Site Name"]),
    FieldMap(to_field="call_sign", converter=None, from_fields=["Call Sign"]),
    FieldMap(
        to_field="fcc_file_number", converter=None, from_fields=["FCC File Number"]
    ),
    FieldMap(
        to_field="latitude", converter=cooerce_lat, from_fields=["LAT (dd mm ss.ss)"]
    ),
    FieldMap(
        to_field="longitude",
        converter=cooerce_long,
        from_fields=["LON (-dd mm ss.ss)", "LON (dd mm ss.ss)"],
    ),
    FieldMap(to_field="amsl", converter=coerce_num, from_fields=["AMSL (m)"]),
    FieldMap(to_field="agl", converter=coerce_num, from_fields=["AGL (m)"]),
    FieldMap(
        to_field="freq_high", converter=coerce_num, from_fields=["Freq High (MHz)"]
    ),
    FieldMap(
        to_field="bandwidth",
        converter=coerce_num,
        from_fields=["Bandwidth (MHz)", "Minimum Bandwidth (MHz) utilized per TX"],
    ),
    FieldMap(
        to_field="max_output",
        converter=coerce_num,
        from_fields=["Max Tx Pwr (W)", "Max Output Pwr (W) Per TX"],
    ),
    FieldMap(
        to_field="antenna_gain", converter=coerce_num, from_fields=["Antenna Gain (dBi)"]
    ),
    FieldMap(
        to_field="system_loss", converter=coerce_num, from_fields=["System Loss (dB)"]
    ),
    FieldMap(
        to_field="main_beam_orientation",
        converter=None,
        from_fields=["Main Beam Orientation (All Sectors)"],
    ),
    FieldMap(
        to_field="mechanical_downtilt",
        converter=None,
        from_fields=["Mechanical Downtilt (All Sectors)"],
    ),
    FieldMap(
        to_field="electrical_downtilt",
        converter=None,
        from_fields=["Electrical Downtilt (All Sectors)"],
    ),
    FieldMap(
        to_field="antenna_model_number", converter=None, from_fields=["Antenna Model #"]
    ),
    # TODO:
    FieldMap(
        to_field="nrqz_id",
        converter=None,
        from_fields=["NRQZ ID (to be assigned by NRAO)", "NRQZ ID"],
    ),
    FieldMap(
        to_field="tx_per_sector",
        converter=coerce_num,
        from_fields=[
            "Number of Transmitters per sector",
            "Total number of TXers (or No. of RRH's ports with feed power) per sector",
            "Number of TXers per sector",
        ],
    ),
    FieldMap(
        to_field="tx_antennas_per_sector",
        converter=coerce_num,
        from_fields=[
            "Number of TX antennas per sector",
            "Number of TX antennas per sector (Each polarization fed with TX power is considered an antenna).",
        ],
    ),
    FieldMap(
        to_field="technology",
        converter=None,
        from_fields=[
            "Technology 2G, 3G, 4G, other (specify)",
            "Technology i.e. FM, 2G, 3G, 4G, GSM, LTE, UMTS, CDMA2000 (specify other)",
        ],
    ),
    FieldMap(
        to_field="uses_split_sectorization",
        converter=coerce_bool,
        from_fields=[
            "This faciltiy uses Split sectorization (Yes or No)",
            "This faciltiy uses Split sectorization (or dual-beam sectorization) Indidate Yes or No",
        ],
    ),
    FieldMap(
        to_field="uses_cross_polarization",
        converter=coerce_bool,
        from_fields=[
            "This facility uses Cross polarization (Yes or No)",
            "This facility uses Cross polarization   Indicate Yes or No",
        ],
    ),
    FieldMap(
        to_field="num_quad_or_octal_ports_with_feed_power",
        converter=coerce_num,
        from_fields=[
            "If this facility uses Quad or Octal polarization, specify type here",
            "Number of Quad or Octal ports with  feed power",
        ],
    ),
    FieldMap(
        to_field="tx_power_pos_45",
        converter=coerce_num,
        from_fields=[
            'If YES to Col. "W", then what is the Max TX output PWR at +45 degrees'
        ],
    ),
    FieldMap(
        to_field="tx_power_neg_45",
        converter=coerce_num,
        from_fields=[
            'If YES to Col. "W", then what is the Max TX output PWR at -45 degrees'
        ],
    ),
    FieldMap(
        to_field="comments",
        converter=None,
        from_fields=["", "Additional information or comments from the applicant"],
    ),
]

# Generate a map of known_header->importer by "expanding" the from_fields of each FieldMap
# In this way we can easily and efficiently look up a given header and find its associated importer
# NOTE: facility_field_map is the primary "export" of this module
facility_field_map = {}
for importer in field_mappers:
    for header in importer.from_fields:
        facility_field_map[header] = importer


if __name__ == "__main__":
    # Print out a simple report of the final header->field mappings
    # header_len is just the longest header in the map plus some padding
    header_len = max(len(header) for header in facility_field_map) + 3
    for header, importer in facility_field_map.items():
        print(f"{header!r:{header_len}}: {importer.to_field!r}")
