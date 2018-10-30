import re

from tools.fieldmap import FieldMap, coerce_num, cooerce_lat, cooerce_long, coerce_bool


# TODO: FieldMap must be able to map a single header to multiple fields. Need to have
# a FieldMaps class (or similar) that holds a list of FieldMaps as well as:
# * a class (e.g. Facility) that will be created
# * ???
field_mappers = [
    FieldMap(
        to_field="freq_low",
        converter=coerce_num,
        from_fields=[
            "Freq Low (MHz)",
            "Freq Low ()",
            "Freq Low (MHz) Frequency specific or lower part of band.",
        ],
    ),
    FieldMap(
        to_field="site_name",
        converter=None,
        from_fields=[
            "Site Name",
            "Site Name       What you call it!",
            "Site Name       What you call it! Include MCN and eNB information.",
            "Sitename",
        ],
    ),
    FieldMap(
        to_field="call_sign",
        converter=None,
        from_fields=["Call Sign", "Call Sign (optional)"],
    ),
    FieldMap(
        to_field="fcc_file_number",
        converter=None,
        from_fields=["FCC File Number", "FCC File Number (if known)", "FCC Fileumber"],
    ),
    FieldMap(
        to_field="latitude",
        converter=cooerce_lat,
        from_fields=[
            "LAT (dd mm ss.ss)",
            "LatN (dd mm ss.ss) Pay close attention to formatting. Spaces required, and NO symbols or special characters!",
            "LatN. Correct submission format is dd mm ss.ss (space seperated).              No symbols or special characters!",
        ],
    ),
    FieldMap(
        to_field="longitude",
        converter=cooerce_long,
        from_fields=[
            "LON (-dd mm ss.ss)",
            "LON (dd mm ss.ss)",
            "LonW (dd mm ss.ss)  Pay close attention to formatting. Spaces required, and NO symbols or special characters!",
            "LonW. Correct submission format is dd mm ss.ss (space seperated).                 No symbols or special characters!",
        ],
    ),
    FieldMap(
        to_field="amsl",
        converter=coerce_num,
        from_fields=["AMSL (m)", "AMSL  (meters)", "AMSL  (meters) Ground elevation"],
    ),
    FieldMap(
        to_field="agl",
        converter=coerce_num,
        from_fields=[
            "AGL (m)",
            "AGL (meters)",
            "AGL (meters) Antenna height to center above ground level",
        ],
    ),
    FieldMap(
        to_field="freq_high",
        converter=coerce_num,
        from_fields=[
            "Freq High (MHz)",
            "Freq High ()",
            "Freq High (MHz)  Frquency specific or upper part of band.",
        ],
    ),
    FieldMap(
        to_field="bandwidth",
        converter=coerce_num,
        from_fields=[
            "Bandwidth (MHz)",
            "Minimum Bandwidth (MHz) utilized per TX",
            "Bandwidth ()",
            "Bandwidth (MHz) Minimum utilized per TX",
            "Bandwidth (MHz) Minimum utilized per TX (i.e. 11K0F0E is a value of 0.011)",
        ],
    ),
    FieldMap(
        to_field="max_output",
        converter=coerce_num,
        from_fields=[
            "Max Tx Pwr (W)",
            "Max Output Pwr (W) Per TX",
            "Max Output Pwr (W)      Per Transmitter or RH",
            "Max Output Pwr (W)      Per Transmitter or RRH (remote radio head) polarization",
        ],
    ),
    FieldMap(
        to_field="antenna_gain",
        converter=coerce_num,
        from_fields=[
            "Antenna Gain (dBi)",
            "11036 ANTenna Gain (dBi)",
            "Antenna Gain ()",
            "Antenna Gain (actual)",
        ],
    ),
    FieldMap(
        to_field="system_loss", converter=coerce_num, from_fields=["System Loss (dB)"]
    ),
    FieldMap(
        to_field="main_beam_orientation",
        converter=None,
        from_fields=[
            "Main Beam Orientation (All Sectors)",
            "Main Beam Orientation or sectorized AZ bearings                              (in ° True NOT                           ° Magnetic)",
        ],
    ),
    FieldMap(
        to_field="mechanical_downtilt",
        converter=None,
        from_fields=["Mechanical Downtilt (All Sectors)", "Mechanical Downtilt"],
    ),
    FieldMap(
        to_field="electrical_downtilt",
        converter=None,
        from_fields=[
            "Electrical Downtilt (All Sectors)",
            "Electrical Downtilt  Sector (Specific and/or RET range)",
            "Electrical Downtilt  Sector specific and/or RET range",
        ],
    ),
    FieldMap(
        to_field="antenna_model_number",
        converter=None,
        from_fields=["Antenna Model #", "11036 ANTenna Model #", "Antenna Model No."],
    ),
    # TODO:
    FieldMap(
        to_field="nrqz_id",
        converter=None,
        from_fields=[
            "NRQZ ID (to be assigned by NRAO)",
            "NRQZ ID",
            "NRQZ ID     (Assigned by NRAO. Do not put any of your data in this column.)",
            "NRQZ ID (to be assigned byRAO)",
        ],
    ),
    FieldMap(
        to_field="tx_per_sector",
        converter=None,
        from_fields=[
            "Number of Transmitters per sector",
            "Total number of TXers (or No. of RRH's ports with feed power) per sector",
            "Number of TXers per sector",
            "Number of TX (or RH's) per sector",
        ],
    ),
    FieldMap(
        to_field="tx_antennas_per_sector",
        converter=None,
        from_fields=[
            "Number of TX antennas per sector",
            "Number of TX antennas per sector (Each polarization fed with TX power is considered an antenna).",
            "Number of Transmit antennas per sector",
            "Number of TX 11036 ANTennas per sector (Each polarization fed with TX power is considered an 11036 ANTenna).",
            "Number of TX antennas per sector (Each polarization fed with TX power is considered an antenna)",
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
            "This faciltiy uses Split sectorization (Yes oro)",
            "This faciltiy uses Split sectorization Indidate Yes or No",
            "This faciltiy uses Split sectorization (or dualbeam sectorization) Indidate Yes or No",
        ],
    ),
    FieldMap(
        to_field="uses_cross_polarization",
        converter=coerce_bool,
        from_fields=[
            "This facility uses Cross polarization (Yes or No)",
            "This facility uses Cross polarization   Indicate Yes or No",
            "This facility uses Cross polarization (Yes oro)",
        ],
    ),
    FieldMap(
        to_field="uses_quad_or_octal_polarization",
        converter=None,
        from_fields=[
            "If this facility uses Quad or Octal polarization, specify type here"
        ],
    ),
    FieldMap(
        to_field="num_quad_or_octal_ports_with_feed_power",
        converter=coerce_num,
        from_fields=["Number of Quad or Octal ports with  feed power"],
    ),
    FieldMap(
        to_field="tx_power_pos_45",
        converter=coerce_num,
        from_fields=[
            'If YES to Col. "W", then what is the Max TX output PWR at +45 degrees',
            # 'If YES to Col. "W", then what is the Max TX output PWR at 45 degrees',
            'If YES to Col. "W", thenhat is the Max TX output PWR at +45 degrees',
        ],
    ),
    FieldMap(
        to_field="tx_power_neg_45",
        converter=coerce_num,
        from_fields=[
            'If YES to Col. "W", then what is the Max TX output PWR at -45 degrees',
            'If YES to Col. "W", thenhat is the Max TX output PWR at -45 degrees',
        ],
    ),
    FieldMap(
        to_field="comments",
        converter=None,
        from_fields=[
            "",
            "Additional information or comments from the applicant",
            "Additional information or comments from the applic11036 ANT",
            "Applicant comments",
        ],
    ),
    # Purposefully ignore all of these headers
    FieldMap(
        to_field=None,
        converter=None,
        from_fields=[
            "Original Row",
            "Applicant",
            "Applicant Name",
            "Name of Applicant",
        ],
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
