"""Field mappings for Excel Data"""

from django.contrib.gis.db.backends.postgis.models import PostGISSpatialRefSys

from django_import_data import (
    FormMap,
    OneToOneFieldMap,
    OneToManyFieldMap,
    ManyToOneFieldMap,
    ManyToManyFieldMap,
)

from cases.forms import AttachmentImportForm, CaseImportForm, FacilityImportForm
from importers.converters import (
    coerce_bool,
    coerce_float,
    coerce_location,
    coerce_positive_float,
    coerce_positive_int,
    convert_freq_high,
    convert_nrqz_id_to_case_num,
    coerce_none,
    convert_mdy_datetime,
)
from utils.constants import EXCEL, NAD83_SRID

IGNORED_HEADERS = [
    "Original Row",
    "Applicant",
    "Applicant Name",
    "Name of Applicant",
    # This is important to allow duplicates for; in fact we depend on that
    # fact for the population of meets_erpd_limit. See below...
    "NRAO AERPd (W)",
    # "Site Inspection Date",
    "Lat1 (dd.dd)N",
    "Lon1 (-dd.dd)W",
]

from datetime import date


def convert_excel_path(path):
    # If the value is a date, then it can't be a path; return None
    if isinstance(path, date):
        return None

    # If the value can be converted to a bool, then it can't be a path; return None
    try:
        coerce_bool(path)
    except ValueError:
        pass
    else:
        return None

    # If the value can be converted to a date, then it can't be a path; return None
    try:
        convert_mdy_datetime(path)
    except ValueError:
        pass
    else:
        return None

    # If the value can be converted to a float, then it can't be a path; return None
    try:
        coerce_float(path)
    except ValueError:
        pass
    else:
        return None

    # If the value has a slash of some kind in it, then it is a path
    if r"\\" or r"/" in path:
        return path

    # Otherwise blow up
    raise ValueError(f"Something is wrong with path value: {path}")


def convert_sgrs_approval(sgrs_approval):
    # If it is already a date, then that's awesome; just use that
    # This also obviously indicates that sgrs_approval should be True
    if isinstance(sgrs_approval, date):
        sgrs_responded_on = sgrs_approval
        sgrs_approval = True
    else:
        # Otherwise, we try two things:
        # 1. Convert to a bool
        try:
            sgrs_approval = coerce_bool(sgrs_approval)
        except ValueError:
            # 2. If that didn't work, convert it to a datetime
            try:
                sgrs_responded_on = convert_mdy_datetime(sgrs_approval)
            except ValueError:
                # 3. If that doesn't work, do a very basic check
                # to see if it's a path or not. If it is, then SGRS has NOT approved!
                if r"\\" or r"/" in sgrs_approval:
                    sgrs_approval = False
                # If it isn't a path, then reject it; something is wrong
                else:
                    # And if that didn't work, raise an error
                    raise ValueError(
                        f"sgrs_approval ({sgrs_approval!r}) couldn't be converted to a date, boolean, or path!"
                    )
                sgrs_responded_on = None
            else:
                # If it did work, sgrs_approval must be true (since we know the date on which they approved)
                sgrs_approval = True
                sgrs_responded_on = None
        else:
            # If we successfully convert to bool, we obviously can't know the date on which they
            # responed (because a bool was there instead of a date)
            sgrs_responded_on = None

    return {"sgrs_approval": sgrs_approval, "sgrs_responded_on": sgrs_responded_on}


def convert_dominant_path(dominant_path):
    if coerce_none(dominant_path) is None:
        return None

    clean_dominant_path = str(dominant_path).strip().lower()
    if not clean_dominant_path:
        return None

    if clean_dominant_path.startswith("d"):
        return "diffraction"
    elif clean_dominant_path.startswith("s"):
        return "scatter"
    elif clean_dominant_path.startswith("f"):
        return "free_space"

    raise ValueError(f"Dominant path {dominant_path} could not be converted!")


def convert_nrao_aerpd(nrao_aerpd, meets_erpd_limit=None):
    """Convert nrqao_aerpd to a float. Convert meets_erpd_limit to a bool"""
    known_meets_erpd_limit_truthy_values = ["meets nrao limit"]
    known_meets_erpd_limit_falsey_values = ["exceedes app requested erpd", "pending"]
    if isinstance(meets_erpd_limit, str):
        clean_meets_erpd_limit = meets_erpd_limit.strip().lower()
        if coerce_none(clean_meets_erpd_limit) is None:
            meets_erpd_limit = False
        elif clean_meets_erpd_limit in known_meets_erpd_limit_truthy_values:
            meets_erpd_limit = True
        elif clean_meets_erpd_limit in known_meets_erpd_limit_falsey_values:
            meets_erpd_limit = False
        else:
            raise ValueError(
                f"meets_erpd_limit ({meets_erpd_limit!r}) is an unknown string value! "
                f"Known values: {known_meets_erpd_limit_truthy_values}"
            )
    else:
        meets_erpd_limit = False

    return {
        "nrao_aerpd": coerce_float(nrao_aerpd),
        "meets_erpd_limit": meets_erpd_limit,
    }


class CaseImportFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            to_field="case_num",
            converter=convert_nrqz_id_to_case_num,
            from_field={
                "nrqz_id": [
                    "NRQZ ID (to be assigned by NRAO)",
                    "NRQZ ID",
                    "NRQZ ID     (Assigned by NRAO. Do not put any of your data in this column.)",
                    "NRQZ ID (to be assigned byRAO)",
                ]
            },
        )
    ]
    form_class = CaseImportForm
    form_defaults = {"data_source": EXCEL}


CASE_FORM_MAP = CaseImportFormMap()


class FacilityImportFormMap(FormMap):
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
            to_field="antenna_gain",
            converter=coerce_positive_float,
            from_field={
                "antenna_gain": [
                    "Antenna Gain (dBi)",
                    "11036 ANTenna Gain (dBi)",
                    "Antenna Gain ()",
                    "Antenna Gain (actual)",
                    "Max Gain (dBi)",
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
            converter=coerce_none,
            from_field={
                "main_beam_orientation": [
                    "Main Beam Orientation (All Sectors)",
                    "Main Beam Orientation or sectorized AZ bearings                              (in ° True NOT                           ° Magnetic)",
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="mechanical_downtilt",
            converter=coerce_none,
            from_field={
                "mechanical_downtilt": [
                    "Mechanical Downtilt (All Sectors)",
                    "Mechanical Downtilt",
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="electrical_downtilt",
            converter=coerce_none,
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
            converter=coerce_none,
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
            to_field="comments",
            from_field={
                "comments": [
                    "",
                    "Additional information or comments from the applicant",
                    "Additional information or comments from the applic11036 ANT",
                    "Applicant comments",
                    "Comments:",
                    "Comments",
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
                "distance_to_first_obstacle": [
                    "Distance to 1st obstacle (km)",
                    "Distance (km) to 1st obstacle",
                ]
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
            to_field="height_of_first_obstacle",
            converter=coerce_positive_float,
            from_field={"height_of_first_obstacle": ["Height of 1st obstacle (ft)"]},
        ),
        OneToOneFieldMap(
            to_field="max_aerpd",
            converter=coerce_positive_float,
            from_field={"max_aerpd": ["Max AERPd (dBm)"]},
        ),
        OneToOneFieldMap(
            to_field="requested_max_erp_per_tx",
            converter=coerce_positive_float,
            from_field={
                "requested_max_erp_per_tx": [
                    # TODO: DUP
                    # "Max ERP per TX (W)",
                    "ERPd per # of Transmitters",
                    "ERPd per TX",
                ]
            },
        ),
        OneToOneFieldMap(
            to_field="max_tx_power",
            converter=coerce_positive_float,
            from_field={
                "max_tx_power": [
                    "Max TX Pwr (W)",
                    "Max Tx Pwr (W)",
                    "Max Output Pwr (W) Per TX",
                    "Max Output Pwr (W)      Per Transmitter or RH",
                    "Max Output Pwr (W)      Per Transmitter or RRH (remote radio head) polarization",
                ]
            },
        ),
        ManyToManyFieldMap(
            to_fields=("nrao_aerpd", "meets_erpd_limit"),
            converter=convert_nrao_aerpd,
            from_fields={
                "nrao_aerpd": "NRAO AERPd (W)",
                # This field is generated by pyexcel in the case where there
                # are two NRAO AERPD (W) columns. We know that the second
                # one is actually a boolean, so it needs to be treated as such
                # TODO: There will be new aliases for this after Paulette has
                # made some tweaks
                "meets_erpd_limit": "NRAO AERPd (W)-1",
            },
            explanation="NRAO AERPd column does double duty: in cases where NRAO approves, "
            "this value will be 'Meets NRAO limit'. In cases where it doesn't, "
            "this value will be the limit itself. So, it needs to map to both "
            "the value field, and the approval field.",
        ),
        OneToOneFieldMap(
            to_field="power_density_limit",
            converter=coerce_none,
            from_field={"power_density_limit": ["Power Density Limit"]},
        ),
        OneToManyFieldMap(
            to_fields=("sgrs_approval", "sgrs_responded_on"),
            converter=convert_sgrs_approval,
            from_field={"sgrs_approval": ["SGRS Approval"]},
        ),
        # TODO: Make attachment somehow?
        OneToOneFieldMap(
            to_field="tap_file", converter=None, from_field={"tap_file": ["TAP file"]}
        ),
        OneToOneFieldMap(
            to_field="tpa", converter=coerce_float, from_field={"tpa": ["TAP", "TPA"]}
        ),
        OneToOneFieldMap(
            to_field="tx_power",
            converter=coerce_positive_float,
            from_field={"tx_power": ["TX Pwr (dBm)"]},
        ),
        OneToOneFieldMap(
            to_field="si_done",
            converter=coerce_positive_float,
            from_field={
                "si_done": [
                    "Inspection Date",
                    "Si Completed",
                    "Site Inspection Completed",
                ]
            },
        ),
    ]
    form_class = FacilityImportForm
    form_defaults = {
        "data_source": EXCEL,
        "original_srs": PostGISSpatialRefSys.objects.get(srid=NAD83_SRID).pk,
    }


FACILITY_FORM_MAP = FacilityImportFormMap()


class SgrsApprovalAttachmentImportFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            to_field="path",
            converter=convert_excel_path,
            from_field={"path": ["SGRS Approval", "SG Approval", "SGRS approval"]},
        )
    ]
    form_class = AttachmentImportForm
    form_defaults = {"data_source": EXCEL, "comments": "SGRS Approval file"}


SGRS_APPROVAL_ATTACHMENT_FORM_MAP = SgrsApprovalAttachmentImportFormMap()


class SiEngineeringAttachmentImportFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            to_field="path",
            converter=convert_excel_path,
            from_field={
                "path": [
                    "SI Worksheet",
                    "SI Engineering",
                    "FEW",
                    "FEW Engineering Worksheet",
                    "FEW - Final Engineering Worksheet",
                    "GBO SI Worksheet",
                    "NRAO SI Worksheet",
                    "SI Inspection Worksheet",
                ]
            },
        )
    ]
    form_class = AttachmentImportForm
    form_defaults = {"data_source": EXCEL, "comments": "FEW file"}


SI_ENGINEERING_ATTACHMENT_FORM_MAP = SiEngineeringAttachmentImportFormMap()


class LocAttachmentImportFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            to_field="path",
            converter=convert_excel_path,
            from_field={"path": ["LOC", "NRAO LOC"]},
        )
    ]
    form_class = AttachmentImportForm
    form_defaults = {"data_source": EXCEL, "comments": "LOC file"}


LOC_ATTACHMENT_FORM_MAP = LocAttachmentImportFormMap()


# PROP STUDY
class TapFileAttachmentImportFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            to_field="path",
            converter=convert_excel_path,
            from_field={"path": ["TAP file", "TAP File"]},
        )
    ]
    form_class = AttachmentImportForm
    form_defaults = {"data_source": EXCEL, "comments": "Propagation Study"}


TAP_FILE_FORM_MAP = TapFileAttachmentImportFormMap()

ATTACHMENT_FORM_MAPS = [
    LOC_ATTACHMENT_FORM_MAP,
    SGRS_APPROVAL_ATTACHMENT_FORM_MAP,
    SI_ENGINEERING_ATTACHMENT_FORM_MAP,
]
