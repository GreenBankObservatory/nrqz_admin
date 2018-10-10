from tools.fieldmap import FieldMap, coerce_num, cooerce_lat, cooerce_long, coerce_bool

field_mappers = [
    FieldMap(field="freq_low", converter=coerce_num, known_headers=["Freq Low (MHz)"]),
    FieldMap(field="site_name", converter=None, known_headers=["Site Name"]),
    FieldMap(field="call_sign", converter=None, known_headers=["Call Sign"]),
    FieldMap(
        field="fcc_file_number", converter=None, known_headers=["FCC File Number"]
    ),
    FieldMap(
        field="latitude", converter=cooerce_lat, known_headers=["LAT (dd mm ss.ss)"]
    ),
    FieldMap(
        field="longitude",
        converter=cooerce_long,
        known_headers=["LON (-dd mm ss.ss)", "LON (dd mm ss.ss)"],
    ),
    FieldMap(field="amsl", converter=coerce_num, known_headers=["AMSL (m)"]),
    FieldMap(field="agl", converter=coerce_num, known_headers=["AGL (m)"]),
    FieldMap(
        field="freq_high", converter=coerce_num, known_headers=["Freq High (MHz)"]
    ),
    FieldMap(
        field="bandwidth",
        converter=coerce_num,
        known_headers=["Bandwidth (MHz)", "Minimum Bandwidth (MHz) utilized per TX"],
    ),
    FieldMap(
        field="max_output",
        converter=coerce_num,
        known_headers=["Max Tx Pwr (W)", "Max Output Pwr (W) Per TX"],
    ),
    FieldMap(
        field="antenna_gain", converter=coerce_num, known_headers=["Antenna Gain (dBi)"]
    ),
    FieldMap(
        field="system_loss", converter=coerce_num, known_headers=["System Loss (dB)"]
    ),
    FieldMap(
        field="main_beam_orientation",
        converter=None,
        known_headers=["Main Beam Orientation (All Sectors)"],
    ),
    FieldMap(
        field="mechanical_downtilt",
        converter=None,
        known_headers=["Mechanical Downtilt (All Sectors)"],
    ),
    FieldMap(
        field="electrical_downtilt",
        converter=None,
        known_headers=["Electrical Downtilt (All Sectors)"],
    ),
    FieldMap(
        field="antenna_model_number", converter=None, known_headers=["Antenna Model #"]
    ),
    FieldMap(
        field="nrqz_id",
        converter=None,
        known_headers=["NRQZ ID (to be assigned by NRAO)", "NRQZ ID"],
    ),
    FieldMap(
        field="tx_per_sector",
        converter=coerce_num,
        known_headers=[
            "Number of Transmitters per sector",
            "Total number of TXers (or No. of RRH's ports with feed power) per sector",
            "Number of TXers per sector",
        ],
    ),
    FieldMap(
        field="tx_antennas_per_sector",
        converter=coerce_num,
        known_headers=[
            "Number of TX antennas per sector",
            "Number of TX antennas per sector (Each polarization fed with TX power is considered an antenna).",
        ],
    ),
    FieldMap(
        field="technology",
        converter=None,
        known_headers=[
            "Technology 2G, 3G, 4G, other (specify)",
            "Technology i.e. FM, 2G, 3G, 4G, GSM, LTE, UMTS, CDMA2000 (specify other)",
        ],
    ),
    FieldMap(
        field="uses_split_sectorization",
        converter=coerce_bool,
        known_headers=[
            "This faciltiy uses Split sectorization (Yes or No)",
            "This faciltiy uses Split sectorization (or dual-beam sectorization) Indidate Yes or No",
        ],
    ),
    FieldMap(
        field="uses_cross_polarization",
        converter=coerce_bool,
        known_headers=[
            "This facility uses Cross polarization (Yes or No)",
            "This facility uses Cross polarization   Indicate Yes or No",
        ],
    ),
    FieldMap(
        field="num_quad_or_octal_ports_with_feed_power",
        converter=coerce_num,
        known_headers=[
            "If this facility uses Quad or Octal polarization, specify type here",
            "Number of Quad or Octal ports with  feed power",
        ],
    ),
    FieldMap(
        field="tx_power_pos_45",
        converter=coerce_num,
        known_headers=[
            'If YES to Col. "W", then what is the Max TX output PWR at +45 degrees'
        ],
    ),
    FieldMap(
        field="tx_power_neg_45",
        converter=coerce_num,
        known_headers=[
            'If YES to Col. "W", then what is the Max TX output PWR at -45 degrees'
        ],
    ),
    FieldMap(
        field="comments",
        converter=None,
        known_headers=["", "Additional information or comments from the applicant"],
    ),
]

# Generate a map of known_header->importer by "expanding" the known_headers of each FieldMap
# In this way we can easily and efficiently look up a given header and find its associated importer
# NOTE: facility_field_map is the primary "export" of this module
facility_field_map = {}
for importer in field_mappers:
    for header in importer.known_headers:
        facility_field_map[header] = importer


if __name__ == "__main__":
    # Print out a simple report of the final header->field mappings
    # header_len is just the longest header in the map plus some padding
    header_len = max(len(header) for header in facility_field_map) + 3
    for header, importer in facility_field_map.items():
        print(f"{header!r:{header_len}}: {importer.field!r}")
