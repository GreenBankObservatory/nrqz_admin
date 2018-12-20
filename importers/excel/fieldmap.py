"""Field mappings for Excel Data"""

import re

from cases.forms import CaseForm, FacilityForm
from importers.fieldmap import FormMap, FieldMap
from importers.converters import coerce_num, coerce_bool


case_regex_str = r"^(?P<case_num>\d+).*"
case_regex = re.compile(case_regex_str)


def coerce_case_num(nrqz_id):
    match = case_regex.match(str(nrqz_id))

    if not match:
        raise ValueError(
            f"Could not parse NRQZ ID '{nrqz_id}' using '{case_regex_str}'!"
        )
    return match["case_num"]


EXCEL = "excel"

CASE_FORM_MAP = FormMap(
    field_maps=[
        FieldMap(
            to_field="case_num",
            converter=coerce_case_num,
            from_fields={
                "nrqz_id": [
                    "NRQZ ID (to be assigned by NRAO)",
                    "NRQZ ID",
                    "NRQZ ID     (Assigned by NRAO. Do not put any of your data in this column.)",
                    "NRQZ ID (to be assigned byRAO)",
                ]
            },
        )
    ],
    form_class=CaseForm,
    form_defaults={"data_source": EXCEL},
)

FACILITY_FORM_MAP = FormMap(
    field_maps=[
        FieldMap(
            to_field="freq_low",
            converter=coerce_num,
            from_fields={
                "freq_low": [
                    "Freq Low (MHz)",
                    "Freq Low ()",
                    "Freq Low (MHz) Frequency specific or lower part of band.",
                ]
            },
        ),
        FieldMap(
            to_field="site_name",
            converter=None,
            from_fields={
                "site_name": [
                    "Site Name",
                    "Site Name       What you call it!",
                    "Site Name       What you call it! Include MCN and eNB information.",
                    "Sitename",
                ]
            },
        ),
        FieldMap(
            to_field="call_sign",
            converter=None,
            from_fields={"call_sign": ["Call Sign", "Call Sign (optional)"]},
        ),
        FieldMap(
            to_field="fcc_file_number",
            converter=None,
            from_fields={
                "fcc_file_number": [
                    "FCC File Number",
                    "FCC File Number (if known)",
                    "FCC Fileumber",
                ]
            },
        ),
        FieldMap(
            to_field="latitude",
            converter=None,
            from_fields={
                "latitude": [
                    "LAT (dd mm ss.ss)",
                    "LatN (dd mm ss.ss) Pay close attention to formatting. Spaces required, and NO symbols or special characters!",
                    "LatN. Correct submission format is dd mm ss.ss (space seperated).              No symbols or special characters!",
                    # Working Data
                    "Lat (dd mm ss.ss)N",
                ]
            },
        ),
        FieldMap(
            to_field="longitude",
            converter=None,
            from_fields={
                "longitude": [
                    "LON (-dd mm ss.ss)",
                    "LON (dd mm ss.ss)",
                    "LonW (dd mm ss.ss)  Pay close attention to formatting. Spaces required, and NO symbols or special characters!",
                    "LonW. Correct submission format is dd mm ss.ss (space seperated).                 No symbols or special characters!",
                    # Working Data
                    "Lon (dd mm ss.ss)W",
                ]
            },
        ),
        FieldMap(
            to_field="amsl",
            converter=coerce_num,
            from_fields={
                "amsl": [
                    "AMSL (m)",
                    "AMSL  (meters)",
                    "AMSL  (meters) Ground elevation",
                    "MSL (m)",
                ]
            },
        ),
        FieldMap(
            to_field="agl",
            converter=coerce_num,
            from_fields={
                "agl": [
                    "AGL (m)",
                    "AGL (meters)",
                    "AGL (meters) Antenna height to center above ground level",
                    # Working Data
                    "AGL",
                ]
            },
        ),
        FieldMap(
            to_field="freq_high",
            converter=coerce_num,
            from_fields={
                "freq_high": [
                    "Freq High (MHz)",
                    "Freq High ()",
                    "Freq High (MHz)  Frquency specific or upper part of band.",
                ]
            },
        ),
        FieldMap(
            to_field="bandwidth",
            converter=coerce_num,
            from_fields={
                "bandwidth": [
                    "Bandwidth (MHz)",
                    "Minimum Bandwidth (MHz) utilized per TX",
                    "Bandwidth ()",
                    "Bandwidth (MHz) Minimum utilized per TX",
                    "Bandwidth (MHz) Minimum utilized per TX (i.e. 11K0F0E is a value of 0.011)",
                ]
            },
        ),
        FieldMap(
            to_field="max_output",
            converter=coerce_num,
            from_fields={
                "max_output": [
                    "Max Tx Pwr (W)",
                    "Max Output Pwr (W) Per TX",
                    "Max Output Pwr (W)      Per Transmitter or RH",
                    "Max Output Pwr (W)      Per Transmitter or RRH (remote radio head) polarization",
                ]
            },
        ),
        FieldMap(
            to_field="antenna_gain",
            converter=coerce_num,
            from_fields={
                "antenna_gain": [
                    "Antenna Gain (dBi)",
                    "11036 ANTenna Gain (dBi)",
                    "Antenna Gain ()",
                    "Antenna Gain (actual)",
                ]
            },
        ),
        FieldMap(
            to_field="system_loss",
            converter=coerce_num,
            from_fields={"system_loss": ["System Loss (dB)", "System Loss (dBi)"]},
        ),
        FieldMap(
            to_field="main_beam_orientation",
            converter=None,
            from_fields={
                "main_beam_orientation": [
                    "Main Beam Orientation (All Sectors)",
                    "Main Beam Orientation or sectorized AZ bearings                              (in ° True NOT                           ° Magnetic)",
                ]
            },
        ),
        FieldMap(
            to_field="mechanical_downtilt",
            converter=None,
            from_fields={
                "mechanical_downtilt": [
                    "Mechanical Downtilt (All Sectors)",
                    "Mechanical Downtilt",
                ]
            },
        ),
        FieldMap(
            to_field="electrical_downtilt",
            converter=None,
            from_fields={
                "electrical_downtilt": [
                    "Electrical Downtilt (All Sectors)",
                    "Electrical Downtilt  Sector (Specific and/or RET range)",
                    "Electrical Downtilt  Sector specific and/or RET range",
                ]
            },
        ),
        FieldMap(
            to_field="antenna_model_number",
            converter=None,
            from_fields={
                "antenna_model_number": [
                    "Antenna Model #",
                    "11036 ANTenna Model #",
                    "Antenna Model No.",
                    "Antenna Model",
                ]
            },
        ),
        # TODO:
        FieldMap(
            to_field="nrqz_id",
            converter=None,
            from_fields={
                "nrqz_id": [
                    "NRQZ ID (to be assigned by NRAO)",
                    "NRQZ ID",
                    "NRQZ ID     (Assigned by NRAO. Do not put any of your data in this column.)",
                    "NRQZ ID (to be assigned byRAO)",
                ]
            },
        ),
        FieldMap(
            to_field="tx_per_sector",
            converter=None,
            from_fields={
                "tx_per_sector": [
                    "Number of Transmitters per sector",
                    "Total number of TXers (or No. of RRH's ports with feed power) per sector",
                    "Number of TXers per sector",
                    "Number of TX (or RH's) per sector",
                    # From Working Data
                    "No TX per facility",
                ]
            },
        ),
        FieldMap(
            to_field="tx_antennas_per_sector",
            converter=None,
            from_fields={
                "tx_antennas_per_sector": [
                    "Number of TX antennas per sector",
                    "Number of TX antennas per sector (Each polarization fed with TX power is considered an antenna).",
                    "Number of Transmit antennas per sector",
                    "Number of TX 11036 ANTennas per sector (Each polarization fed with TX power is considered an 11036 ANTenna).",
                    "Number of TX antennas per sector (Each polarization fed with TX power is considered an antenna)",
                ]
            },
        ),
        FieldMap(
            to_field="technology",
            converter=None,
            from_fields={
                "technology": [
                    "Technology 2G, 3G, 4G, other (specify)",
                    "Technology i.e. FM, 2G, 3G, 4G, GSM, LTE, UMTS, CDMA2000 (specify other)",
                ]
            },
        ),
        FieldMap(
            to_field="uses_split_sectorization",
            converter=coerce_bool,
            from_fields={
                "uses_split_sectorization": [
                    "This faciltiy uses Split sectorization (Yes or No)",
                    "This faciltiy uses Split sectorization (or dual-beam sectorization) Indidate Yes or No",
                    "This faciltiy uses Split sectorization (Yes oro)",
                    "This faciltiy uses Split sectorization Indidate Yes or No",
                    "This faciltiy uses Split sectorization (or dualbeam sectorization) Indidate Yes or No",
                ]
            },
        ),
        FieldMap(
            to_field="uses_cross_polarization",
            converter=coerce_bool,
            from_fields={
                "uses_cross_polarization": [
                    "This facility uses Cross polarization (Yes or No)",
                    "This facility uses Cross polarization   Indicate Yes or No",
                    "This facility uses Cross polarization (Yes oro)",
                ]
            },
        ),
        FieldMap(
            to_field="uses_quad_or_octal_polarization",
            converter=None,
            from_fields={
                "uses_quad_or_octal_polarization": [
                    "If this facility uses Quad or Octal polarization, specify type here"
                ]
            },
        ),
        FieldMap(
            to_field="num_quad_or_octal_ports_with_feed_power",
            converter=coerce_num,
            from_fields={
                "num_quad_or_octal_ports_with_feed_power": [
                    "Number of Quad or Octal ports with  feed power"
                ]
            },
        ),
        FieldMap(
            to_field="tx_power_pos_45",
            converter=coerce_num,
            from_fields={
                "tx_power_pos_45": [
                    'If YES to Col. "W", then what is the Max TX output PWR at +45 degrees',
                    # 'If YES to Col. "W", then what is the Max TX output PWR at 45 degrees',
                    'If YES to Col. "W", thenhat is the Max TX output PWR at +45 degrees',
                ]
            },
        ),
        FieldMap(
            to_field="tx_power_neg_45",
            converter=coerce_num,
            from_fields={
                "tx_power_neg_45": [
                    'If YES to Col. "W", then what is the Max TX output PWR at -45 degrees',
                    'If YES to Col. "W", thenhat is the Max TX output PWR at -45 degrees',
                ]
            },
        ),
        FieldMap(
            to_field="comments",
            converter=None,
            from_fields={
                "comments": [
                    "",
                    "Additional information or comments from the applicant",
                    "Additional information or comments from the applic11036 ANT",
                    "Applicant comments",
                ]
            },
        ),
        # Purposefully ignore all of these headers
        # FieldMap(
        #     to_field=None,
        #     converter=None,
        #     from_fields={
        #         "None": [
        #             "Original Row",
        #             "Applicant",
        #             "Applicant Name",
        #             "Name of Applicant",
        #         ]
        #     },
        # ),
        # From Working Data
        FieldMap(
            to_field="num_tx_per_facility",
            converter=None,
            from_fields={
                "num_tx_per_facility": [
                    "# of TX per facility",
                    "# TX per facility",
                    "No TX per facility",
                ]
            },
        ),
        FieldMap(
            to_field="aeirp_to_gbt",
            converter=None,
            from_fields={"aeirp_to_gbt": ["AEiRP to GBT"]},
        ),
        FieldMap(
            to_field="az_bearing",
            converter=None,
            from_fields={"az_bearing": ["AZ bearing degrees True"]},
        ),
        FieldMap(
            to_field="band_allowance",
            converter=None,
            from_fields={"band_allowance": ["Band Allowance"]},
        ),
        FieldMap(
            to_field="distance_to_first_obstacle",
            converter=None,
            from_fields={
                "distance_to_first_obstacle": ["Distance to 1st obstacle (km)"]
            },
        ),
        FieldMap(
            to_field="dominant_path",
            converter=None,
            from_fields={
                "dominant_path": [
                    "Dominant path",
                    "Dominant Path",
                    "Domanant path (D or S)",
                ]
            },
        ),
        FieldMap(
            to_field="erpd_per_num_tx",
            converter=None,
            from_fields={
                "erpd_per_num_tx": ["ERPd per # of Transmitters", "ERPd per TX"]
            },
        ),
        FieldMap(
            to_field="height_of_first_obstacle",
            converter=None,
            from_fields={"height_of_first_obstacle": ["Height of 1st obstacle (ft)"]},
        ),
        FieldMap(to_field="loc", converter=None, from_fields={"loc": ["LOC"]}),
        FieldMap(
            to_field="max_aerpd",
            converter=None,
            from_fields={"max_aerpd": ["Max AERPd (dBm)"]},
        ),
        FieldMap(
            to_field="max_erp_per_tx",
            converter=None,
            from_fields={"max_erp_per_tx": ["Max ERP per TX (W)"]},
        ),
        FieldMap(
            to_field="max_gain",
            converter=None,
            from_fields={"max_gain": ["Max Gain (dBi)"]},
        ),
        FieldMap(
            to_field="max_tx_power",
            converter=None,
            from_fields={"max_tx_power": ["Max TX Pwr (W)"]},
        ),
        FieldMap(
            to_field="nrao_aerpd",
            converter=None,
            from_fields={"nrao_aerpd": ["NRAO AERPd (W)"]},
        ),
        FieldMap(
            to_field="power_density_limit",
            converter=None,
            from_fields={"power_density_limit": ["Power Density Limit"]},
        ),
        FieldMap(
            to_field="sgrs_approval",
            converter=None,
            from_fields={"sgrs_approval": ["SGRS Approval"]},
        ),
        FieldMap(
            to_field="tap_file", converter=None, from_fields={"tap_file": ["TAP file"]}
        ),
        FieldMap(to_field="tap", converter=None, from_fields={"tap": ["TAP", "TPA"]}),
        FieldMap(
            to_field="tx_power",
            converter=None,
            from_fields={"tx_power": ["TX Pwr (dBm)"]},
        ),
    ],
    form_class=FacilityForm,
    form_defaults={"data_source": EXCEL},
)

# Generate a map of known_header->importer by "expanding" the from_fields {"": of each FieldMap
# In this way we can easily and efficiently look up a given header and find its associated importer
# NOTE: facility_field_map is the primary "export" of this module
# facility_field_map = {}
# for importer in field_mappers:
#     for header in importer.from_field_aliases:
#         facility_field_map[header] = importer


# def gen_header_field_map(headers):
#     header_field_map = OrderedDict(
#         [(header, FACILITY_FORM_MAP.get(header, None)) for header in headers]
#     )
#     return header_field_map


# def get_unmapped_headers(header_field_map):
#     return [header for header, field in header_field_map.items() if field is None]


# if __name__ == "__main__":
#     # Print out a simple report of the final header->field mappings
#     # header_len is just the longest header in the map plus some padding
#     header_len = max(len(header) for header in facility_field_map) + 3
#     for header, importer in facility_field_map.items():
#         print(f"{header!r:{header_len}}: {importer.to_field!r}")
