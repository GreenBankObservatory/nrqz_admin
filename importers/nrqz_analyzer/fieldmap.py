"""Field mappings for NRQZ Analyzer Data"""

import re

from django_import_data import FormMap, OneToOneFieldMap, ManyToOneFieldMap

from cases.forms import CaseForm, FacilityForm, StructureForm

from importers.converters import (
    coerce_location,
    convert_nrqz_id_to_case_num,
    coerce_float,
    coerce_positive_float,
    convert_freq_high,
    coerce_bool,
)
from utils.constants import NAM_APPLICATION


def convert_street(caddr=None, caddr2=None):
    parts = []
    if caddr:
        parts.append(caddr)
    if caddr2:
        parts.append(caddr2)
    return " ".join(parts)


def convert_to_bandwidth(sysBW=None, sysType=None):
    if not (sysBW or sysType):
        return None

    if sysBW and sysType:
        raise ValueError("Cannot have both sysBW and sysType!")

    return sysBW or sysType


def convert_agency_num(AgencyNo):
    return AgencyNo


def convert_to_system_loss(lbot=None, ltl=None, ltop=None):
    if not any([lbot, ltl, ltop]):
        return None

    if not all([lbot, ltl, ltop]):
        raise ValueError(
            "Either all values or no values must be given! "
            f"lbot: {lbot}, ltl: {ltl}, ltop: {ltop}"
        )
    return float(lbot) + float(ltl) + float(ltop)


def convert_tpa(tpa):
    clean_tpa = re.sub(r"[^0-9\.]", "", tpa)
    if not clean_tpa:
        return None
    return float(clean_tpa)


class CaseFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            from_field="nrqzID",
            converter=convert_nrqz_id_to_case_num,
            to_field="case_num",
        ),
        # TODO: Should this base Facility-level?
        OneToOneFieldMap(from_field="service", to_field="radio_service"),
    ]
    form_class = CaseForm
    form_defaults = {"data_source": NAM_APPLICATION}


class FacilityFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(from_field="nrqzID", to_field="nrqz_id"),
        OneToOneFieldMap(
            from_field="nrqzID",
            converter=convert_nrqz_id_to_case_num,
            to_field="case_num",
        ),
        ManyToOneFieldMap(
            from_fields={"latitude": ["lat"], "longitude": ["lon"]},
            converter=coerce_location,
            to_field="location",
        ),
        OneToOneFieldMap(from_field="gnd", to_field="amsl"),
        OneToOneFieldMap(
            from_field="freq", converter=coerce_positive_float, to_field="freq_low"
        ),
        ManyToOneFieldMap(
            from_fields={"freq_low": "freq", "freq_high": "BandHi"},
            converter=convert_freq_high,
            to_field="freq_high",
        ),
        ManyToOneFieldMap(
            from_fields=("sysBW", "sysType"),
            converter=convert_to_bandwidth,
            to_field="bandwidth",
        ),
        OneToOneFieldMap(
            from_field={"sitename": ("sitename", "site_name")}, to_field="site_name"
        ),
        # TODO
        OneToOneFieldMap(from_field="fccfn", to_field="fcc_file_num"),
        OneToOneFieldMap(from_field="call", to_field="call_sign"),
        OneToOneFieldMap(
            from_field="mxtxpo", converter=coerce_float, to_field="max_tx_power"
        ),
        OneToOneFieldMap(
            from_field="AgencyNo", converter=convert_agency_num, to_field="agency_num"
        ),
        OneToOneFieldMap(from_field="aaz", to_field="main_beam_orientation"),
        OneToOneFieldMap(
            from_field="agl", converter=coerce_positive_float, to_field="agl"
        ),
        OneToOneFieldMap(
            from_field="ebt",
            converter=coerce_positive_float,
            to_field="electrical_downtilt",
            explanation="Still a little fuzzy on this one...",
        ),
        OneToOneFieldMap(from_field="type", to_field="antenna_model_number"),
        ManyToOneFieldMap(
            from_fields=("lbot", "ltl", "ltop"),
            converter=convert_to_system_loss,
            to_field="system_loss",
        ),
        OneToOneFieldMap(
            from_field="mbt",
            converter=coerce_positive_float,
            to_field="mechanical_downtilt",
            explanation="Still a little fuzzy on this one...",
        ),
        OneToOneFieldMap(
            from_field="mxg",
            converter=coerce_positive_float,
            to_field="max_gain",
            explanation="Still a little fuzzy on this one (dB, dBi?)",
        ),
        OneToOneFieldMap(
            from_field="o1dis",
            converter=coerce_positive_float,
            to_field="distance_to_first_obstacle",
        ),
        OneToOneFieldMap(
            from_field="o1elev",
            converter=coerce_positive_float,
            to_field="height_of_first_obstacle",
        ),
        OneToOneFieldMap(
            from_field="qzpwrde",
            converter=coerce_positive_float,
            to_field="power_density_limit",
        ),
        OneToOneFieldMap(from_field="tpa", converter=convert_tpa, to_field="tpa"),
        OneToOneFieldMap(
            from_field="txpo",
            converter=coerce_positive_float,
            to_field="tx_power",
            explanation="Paulette said this should map to max tx power, but I have a separate field for tx power....",
        ),
        OneToOneFieldMap(
            from_field={"fed": "Fed"}, converter=coerce_bool, to_field="fed"
        ),
        # NOTE: This is "synthetic", in the sense that there is no one "comments"
        # column. See import_nam_application for details
        OneToOneFieldMap("comments"),
    ]
    form_class = FacilityForm
    form_defaults = {"data_source": NAM_APPLICATION}


# class StructureFormMap(FormMap):
#     field_maps = [OneToOneFieldMap("asr")]
#     form_class = StructureForm
#     form_defaults = {"data_source": NAM_APPLICATION}


CASE_FORM_MAP = CaseFormMap()
FACILITY_FORM_MAP = FacilityFormMap()
# STRUCTURE_FORM_MAP = StructureFormMap()

IGNORED_HEADERS = [
    "06DEC10",
    "06OCT2011",
    "09SEP11",
    "1-ASurvey",
    "12APR11",
    "18 June 2012",
    "19JAN11",
    "2-CSurvey",
    "25JAN11",
    "27JAN11",
    "28JAN11",
    "5601 LEGACY DRIVE, MS",
    "action",
    "AlterableBW",
    "AlterablePan",
    "AlterableTilt",
    "amanuf",
    "Antennas",
    "appcomplete",
    "asr",
    "azgbt",
    "bcomp",
    "botcomp",
    "caddr",
    "caddr2",
    "camendate",
    "caplname",
    "ccell",
    "ccphone",
    "ccty",
    "cemail",
    "cfax",
    "cityst",
    "cnumber",
    "completeDate",
    "cperson",
    "cst",
    "czip",
    "data",
    "ga2gbt",
    "gps",
    "ha",
    "legalname",
    "Lfs",
    "nant",
    "NoRDate",
    "NoRnumber",
    "purpose",
    "Rad Center 245 ft x 0.3048 = 74.676 m.  Tower FCC Reg #",
    "receivedDate",
    "SGobjects",
    "sgrs",
    "siWaived",
    "tcomp",
    "topcomp",
    "txmanuf",
]
