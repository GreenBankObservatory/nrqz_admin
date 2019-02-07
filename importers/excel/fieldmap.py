"""Field mappings for Excel Data"""

from django_import_data import (
    FormMap,
    OneToOneFieldMap,
    OneToManyFieldMap,
    ManyToOneFieldMap,
    ManyToManyFieldMap,
)

from cases.forms import CaseForm, FacilityForm
from importers.converters import (
    coerce_bool,
    coerce_float,
    coerce_location,
    coerce_positive_float,
    coerce_positive_int,
    convert_freq_high,
    convert_nrqz_id_to_case_num,
)
from utils.constants import EXCEL

IGNORED_HEADERS = [
    "Original Row",
    "Applicant",
    "Applicant Name",
    "Name of Applicant",
    # This is important to allow duplicates for; in fact we depend on that
    # fact for the population of nrao_approval. See below...
    "NRAO AERPd (W)",
]


def convert_dominant_path(dominant_path):
    clean_dominant_path = dominant_path.strip().lower()
    if not clean_dominant_path:
        return None

    if clean_dominant_path.startswith("d"):
        return "diffraction"
    elif clean_dominant_path.startswith("s"):
        return "scatter"
    elif clean_dominant_path.startswith("f"):
        return "free_space"

    raise ValueError(f"Dominant path {dominant_path} could not be converted!")


def convert_nrao_aerpd(nrao_aerpd, nrao_approval=None):
    """Convert nrqao_aerpd to a float. Convert nrao_approval to a bool"""
    known_truthy_values = ["meets nrao limit"]
    if isinstance(nrao_approval, str):
        clean_nrao_approval = nrao_approval.strip().lower()
        if clean_nrao_approval in known_truthy_values:
            nrao_approval = True
        else:
            raise ValueError(
                f"nrao_aerpd ({nrao_aerpd}) is an unknown string value! "
                f"Known values: {known_truthy_values}"
            )
    else:
        nrao_approval = False

    return {"nrao_aerpd": float(nrao_aerpd), "nrao_approval": nrao_approval}


class CaseFormMap(FormMap):
    field_maps = [
        ManyToOneFieldMap(
            to_field="case_num",
            converter=convert_nrqz_id_to_case_num,
            from_fields={
                "nrqz_id": [
                    "NRQZ ID (to be assigned by NRAO)",
                    "NRQZ ID",
                    "NRQZ ID     (Assigned by NRAO. Do not put any of your data in this column.)",
                    "NRQZ ID (to be assigned byRAO)",
                ],
                "loc": ["LOC"],
            },
        )
    ]
    form_class = CaseForm
    form_defaults = {"data_source": EXCEL}


CASE_FORM_MAP = CaseFormMap()


class FacilityFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            to_field="freq_low",
            converter=coerce_positive_float,
            from_field={
                # TODO: Consolidate!
                "freq_low": [
                    "Freq Low (MHz)",
                    "Freq Low ()",
                    "Freq Low (MHz) Frequency specific or lower part of band.",
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="site_name",
            from_field={
                "site_name": [
                    "Site Name",
                    "Site Name       What you call it!",
                    "Site Name       What you call it! Include MCN and eNB information.",
                    "Sitename",
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="call_sign",
            from_field={"call_sign": ["Call Sign", "Call Sign (optional)"]},
        ),
        OneToOneFieldMap(
            to_field="fcc_file_number",
            from_field={
                "fcc_file_number": [
                    "FCC File Number",
                    "FCC File Number (if known)",
                    "FCC Fileumber",
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="latitude",
            # TODO: CONSOLIDATE
            from_field={
                "latitude": [
                    "LAT (dd mm ss.ss)",
                    "LatN (dd mm ss.ss) Pay close attention to formatting. Spaces required, and NO symbols or special characters!",
                    "LatN. Correct submission format is dd mm ss.ss (space seperated).              No symbols or special characters!",
                    # Working Data
                    "Lat (dd mm ss.ss)N",
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="longitude",
            # TODO: CONSOLIDATE
            from_field={
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
        ManyToOneFieldMap(
            to_field="location",
            converter=coerce_location,
            # TODO: CONSOLIDATE
            from_fields={
                "latitude": [
                    "LAT (dd mm ss.ss)",
                    "LatN (dd mm ss.ss) Pay close attention to formatting. Spaces required, and NO symbols or special characters!",
                    "LatN. Correct submission format is dd mm ss.ss (space seperated).              No symbols or special characters!",
                    # Working Data
                    "Lat (dd mm ss.ss)N",
                    "LatN (dd mm ss.ss)N",
                ],
                "longitude": [
                    "LON (-dd mm ss.ss)",
                    "LON (dd mm ss.ss)",
                    "LonW (dd mm ss.ss)  Pay close attention to formatting. Spaces required, and NO symbols or special characters!",
                    "LonW. Correct submission format is dd mm ss.ss (space seperated).                 No symbols or special characters!",
                    # Working Data
                    "Lon (dd mm ss.ss)W",
                    "LonW (dd mm ss.ss)W",
                ],
            },
        ),
        OneToOneFieldMap(
            to_field="amsl",
            converter=coerce_positive_float,
            from_field={
                "amsl": [
                    "AMSL (m)",
                    "AMSL  (meters)",
                    "AMSL  (meters) Ground elevation",
                    "MSL (m)",
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="agl",
            converter=coerce_positive_float,
            from_field={
                "agl": [
                    "AGL (m)",
                    "AGL (meters)",
                    "AGL (meters) Antenna height to center above ground level",
                    # Working Data
                    "AGL",
                ]
            },
        ),
        ManyToOneFieldMap(
            to_field="freq_high",
            converter=convert_freq_high,
            from_fields={
                # TODO: Consolidate!
                "freq_low": [
                    "Freq Low (MHz)",
                    "Freq Low ()",
                    "Freq Low (MHz) Frequency specific or lower part of band.",
                ],
                "freq_high": [
                    "Freq High (MHz)",
                    "Freq High ()",
                    "Freq High (MHz)  Frquency specific or upper part of band.",
                ],
            },
        ),
        OneToOneFieldMap(
            to_field="bandwidth",
            converter=coerce_positive_float,
            from_field={
                "bandwidth": [
                    "Bandwidth (MHz)",
                    "Minimum Bandwidth (MHz) utilized per TX",
                    "Bandwidth ()",
                    "Bandwidth (MHz) Minimum utilized per TX",
                    "Bandwidth (MHz) Minimum utilized per TX (i.e. 11K0F0E is a value of 0.011)",
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="max_output",
            converter=coerce_positive_float,
            from_field={
                "max_output": [
                    "Max Tx Pwr (W)",
                    "Max Output Pwr (W) Per TX",
                    "Max Output Pwr (W)      Per Transmitter or RH",
                    "Max Output Pwr (W)      Per Transmitter or RRH (remote radio head) polarization",
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="antenna_gain",
            converter=coerce_positive_float,
            from_field={
                "antenna_gain": [
                    "Antenna Gain (dBi)",
                    "11036 ANTenna Gain (dBi)",
                    "Antenna Gain ()",
                    "Antenna Gain (actual)",
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="system_loss",
            converter=coerce_positive_float,
            from_field={"system_loss": ["System Loss (dB)", "System Loss (dBi)"]},
        ),
        OneToOneFieldMap(
            to_field="main_beam_orientation",
            converter=coerce_positive_float,
            from_field={
                "main_beam_orientation": [
                    "Main Beam Orientation (All Sectors)",
                    "Main Beam Orientation or sectorized AZ bearings                              (in ° True NOT                           ° Magnetic)",
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="mechanical_downtilt",
            converter=coerce_positive_float,
            from_field={
                "mechanical_downtilt": [
                    "Mechanical Downtilt (All Sectors)",
                    "Mechanical Downtilt",
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="electrical_downtilt",
            converter=coerce_positive_float,
            from_field={
                "electrical_downtilt": [
                    "Electrical Downtilt (All Sectors)",
                    "Electrical Downtilt  Sector (Specific and/or RET range)",
                    "Electrical Downtilt  Sector specific and/or RET range",
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="antenna_model_number",
            from_field={
                "antenna_model_number": [
                    "Antenna Model #",
                    "11036 ANTenna Model #",
                    "Antenna Model No.",
                    "Antenna Model",
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="nrqz_id",
            from_field={
                "nrqz_id": [
                    "NRQZ ID (to be assigned by NRAO)",
                    "NRQZ ID",
                    "NRQZ ID     (Assigned by NRAO. Do not put any of your data in this column.)",
                    "NRQZ ID (to be assigned byRAO)",
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="tx_per_sector",
            converter=coerce_positive_int,
            from_field={
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
        OneToOneFieldMap(
            to_field="tx_antennas_per_sector",
            converter=coerce_positive_int,
            from_field={
                "tx_antennas_per_sector": [
                    "Number of TX antennas per sector",
                    "Number of TX antennas per sector (Each polarization fed with TX power is considered an antenna).",
                    "Number of Transmit antennas per sector",
                    "Number of TX 11036 ANTennas per sector (Each polarization fed with TX power is considered an 11036 ANTenna).",
                    "Number of TX antennas per sector (Each polarization fed with TX power is considered an antenna)",
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="technology",
            from_field={
                "technology": [
                    "Technology 2G, 3G, 4G, other (specify)",
                    "Technology i.e. FM, 2G, 3G, 4G, GSM, LTE, UMTS, CDMA2000 (specify other)",
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="uses_split_sectorization",
            converter=coerce_bool,
            from_field={
                "uses_split_sectorization": [
                    "This faciltiy uses Split sectorization (Yes or No)",
                    "This faciltiy uses Split sectorization (or dual-beam sectorization) Indidate Yes or No",
                    "This faciltiy uses Split sectorization (Yes oro)",
                    "This faciltiy uses Split sectorization Indidate Yes or No",
                    "This faciltiy uses Split sectorization (or dualbeam sectorization) Indidate Yes or No",
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="uses_cross_polarization",
            converter=coerce_bool,
            from_field={
                "uses_cross_polarization": [
                    "This facility uses Cross polarization (Yes or No)",
                    "This facility uses Cross polarization   Indicate Yes or No",
                    "This facility uses Cross polarization (Yes oro)",
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="uses_quad_or_octal_polarization",
            converter=coerce_bool,
            from_field={
                "uses_quad_or_octal_polarization": [
                    "If this facility uses Quad or Octal polarization, specify type here"
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="num_quad_or_octal_ports_with_feed_power",
            converter=coerce_float,
            from_field={
                "num_quad_or_octal_ports_with_feed_power": [
                    "Number of Quad or Octal ports with  feed power"
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="tx_power_pos_45",
            converter=coerce_float,
            from_field={
                "tx_power_pos_45": [
                    'If YES to Col. "W", then what is the Max TX output PWR at +45 degrees',
                    # 'If YES to Col. "W", then what is the Max TX output PWR at 45 degrees',
                    'If YES to Col. "W", thenhat is the Max TX output PWR at +45 degrees',
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="tx_power_neg_45",
            converter=coerce_float,
            from_field={
                "tx_power_neg_45": [
                    'If YES to Col. "W", then what is the Max TX output PWR at -45 degrees',
                    'If YES to Col. "W", thenhat is the Max TX output PWR at -45 degrees',
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="comments",
            from_field={
                "comments": [
                    "",
                    "Additional information or comments from the applicant",
                    "Additional information or comments from the applic11036 ANT",
                    "Applicant comments",
                ]
            },
        ),
        # From Working Data
        OneToOneFieldMap(
            to_field="num_tx_per_facility",
            converter=coerce_positive_int,
            from_field={
                "num_tx_per_facility": [
                    "# of TX per facility",
                    "# TX per facility",
                    "No TX per facility",
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="aeirp_to_gbt",
            converter=coerce_positive_float,
            from_field={"aeirp_to_gbt": ["AEiRP to GBT"]},
        ),
        OneToOneFieldMap(
            to_field="az_bearing",
            converter=coerce_positive_float,
            from_field={"az_bearing": ["AZ bearing degrees True"]},
        ),
        OneToOneFieldMap(
            to_field="band_allowance",
            converter=coerce_positive_float,
            from_field={"band_allowance": ["Band Allowance"]},
        ),
        OneToOneFieldMap(
            to_field="distance_to_first_obstacle",
            converter=coerce_positive_float,
            from_field={
                "distance_to_first_obstacle": ["Distance to 1st obstacle (km)"]
            },
        ),
        OneToOneFieldMap(
            to_field="dominant_path",
            converter=convert_dominant_path,
            from_field={
                "dominant_path": [
                    "Dominant path",
                    "Dominant Path",
                    "Domanant path (D or S)",
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="erpd_per_num_tx",
            converter=coerce_positive_float,
            from_field={
                "erpd_per_num_tx": ["ERPd per # of Transmitters", "ERPd per TX"]
            },
        ),
        OneToOneFieldMap(
            to_field="height_of_first_obstacle",
            converter=coerce_positive_float,
            from_field={"height_of_first_obstacle": ["Height of 1st obstacle (ft)"]},
        ),
        OneToOneFieldMap(to_field="loc", converter=None, from_field={"loc": ["LOC"]}),
        OneToOneFieldMap(
            to_field="max_aerpd",
            converter=coerce_positive_float,
            from_field={"max_aerpd": ["Max AERPd (dBm)"]},
        ),
        OneToOneFieldMap(
            to_field="max_erp_per_tx",
            converter=coerce_positive_float,
            from_field={"max_erp_per_tx": ["Max ERP per TX (W)"]},
        ),
        OneToOneFieldMap(
            to_field="max_gain",
            converter=coerce_positive_float,
            from_field={"max_gain": ["Max Gain (dBi)"]},
        ),
        OneToOneFieldMap(
            to_field="max_tx_power",
            converter=coerce_positive_float,
            from_field={"max_tx_power": ["Max TX Pwr (W)"]},
        ),
        ManyToManyFieldMap(
            to_fields=("nrao_aerpd", "nrao_approval"),
            converter=convert_nrao_aerpd,
            from_fields={
                "nrao_aerpd": "NRAO AERPd (W)",
                # This field is generated by pyexcel in the case where there
                # are two NRAO AERPD (W) columns. We know that the second
                # one is actually a boolean, so it needs to be treated as such
                # TODO: There will be new aliases for this after Paulette has
                # made some tweaks
                "nrao_approval": "NRAO AERPd (W)-1",
            },
            explanation="NRAO AERPd column does double duty: in cases where NRAO approves, "
            "this value will be 'Meets NRAO limit'. In cases where it doesn't, "
            "this value will be the limit itself. So, it needs to map to both "
            "the value field, and the approval field.",
        ),
        OneToOneFieldMap(
            to_field="power_density_limit",
            converter=coerce_positive_float,
            from_field={"power_density_limit": ["Power Density Limit"]},
        ),
        OneToOneFieldMap(
            to_field="sgrs_approval",
            converter=coerce_bool,
            from_field={"sgrs_approval": ["SGRS Approval"]},
        ),
        # TODO: Make attachment somehow?
        OneToOneFieldMap(
            to_field="tap_file", converter=None, from_field={"tap_file": ["TAP file"]}
        ),
        OneToOneFieldMap(
            to_field="tpa", converter=None, from_field={"tpa": ["TAP", "TPA"]}
        ),
        OneToOneFieldMap(
            to_field="tx_power",
            converter=coerce_positive_float,
            from_field={"tx_power": ["TX Pwr (dBm)"]},
        ),
    ]
    form_class = FacilityForm
    form_defaults = {"data_source": EXCEL}


FACILITY_FORM_MAP = FacilityFormMap()
