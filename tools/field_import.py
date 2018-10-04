def coerce_bool(value):
    clean_value = value.strip().lower()
    if clean_value.startswith("yes"):
        return True
    elif clean_value.startswith("no"):
        return False
    elif clean_value in ["", "na"]:
        return None
    else:
        raise ValueError("Could not determine truthiness of value {!r}".format(value))


def coerce_num(value):
    if value in ["", "na", "n/a", "no"]:
        return None
    return value


class FieldImport:
    def __init__(self, field, converter, known_headers):
        # Headers the field could potentially be associated with
        self.field = field
        # Function to convert/clean data
        self.converter = converter if converter else self.default_converter
        self.known_headers = known_headers

    def default_converter(self, value):
        return value

    def __repr__(self):
        return f"{self.field} <{self.converter.__name__}>: {self.known_headers}"

    # def process(self, ):


field_importers = [
    FieldImport(
        field="freq_low", converter=coerce_num, known_headers=["Freq Low (MHz)"]
    ),
    FieldImport(field="site_name", converter=None, known_headers=["Site Name"]),
    FieldImport(field="call_sign", converter=None, known_headers=["Call Sign"]),
    FieldImport(
        field="fcc_file_number", converter=None, known_headers=["FCC File Number"]
    ),
    FieldImport(field="latitude", converter=None, known_headers=["LAT (dd mm ss.ss)"]),
    FieldImport(
        field="longitude",
        converter=None,
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
facility_field_map = {}
for importer in field_importers:
    for header in importer.known_headers:
        facility_field_map[header] = importer


if __name__ == '__main__':
    header_len = max(len(header) for header in facility_field_map) + 3
    for header, importer in facility_field_map.items():
        print(f"{header!r:{header_len}}: {importer.field!r}")
