"""Field mappings for Access Preliminary Technical Data"""
from cases.forms import PersonForm, PreliminaryCaseForm, PreliminaryFacilityForm

from django_import_data import OneToOneFieldMap, ManyToOneFieldMap, FormMap
from importers.converters import (
    coerce_scientific_notation,
    coerce_none,
    coerce_feet_to_meters,
    coerce_location,
)
from importers.access_application.fieldmap import coerce_datetime, coerce_positive_int

ACCESS_PRELIM_TECHNICAL = "access_prelim_technical"


class ApplicantFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(to_field="name", converter=None, from_field="APPLICANT")
    ]
    form_class = PersonForm
    form_defaults = {"data_source": ACCESS_PRELIM_TECHNICAL}


class PcaseFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            to_field="case_num", converter=coerce_positive_int, from_field="PNRQZ_NO"
        )
    ]
    form_class = PreliminaryCaseForm
    form_defaults = {"data_source": ACCESS_PRELIM_TECHNICAL}


class PfacilityFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            to_field="site_num", converter=coerce_positive_int, from_field="Site Number"
        ),
        OneToOneFieldMap(
            to_field="original_created_on", converter=coerce_datetime, from_field="DATE"
        ),
        OneToOneFieldMap(to_field="freq_low", converter=None, from_field="FREQUENCY"),
        OneToOneFieldMap(
            to_field="antenna_model_number", converter=None, from_field="ANT_MODEL"
        ),
        OneToOneFieldMap(
            to_field="power_density_limit",
            converter=coerce_scientific_notation,
            from_field="PWD_LIMIT",
        ),
        OneToOneFieldMap(to_field="site_name", converter=None, from_field="LOCATION"),
        OneToOneFieldMap(
            to_field="latitude", converter=coerce_none, from_field="LATITUDE"
        ),
        OneToOneFieldMap(
            to_field="longitude", converter=coerce_none, from_field="LONGITUDE"
        ),
        ManyToOneFieldMap(
            to_field="location",
            converter=coerce_location,
            from_fields=({"latitude": ("LATITUDE",), "longitude": ("LONGITUDE",)}),
        ),
        OneToOneFieldMap(
            to_field="amsl", converter=coerce_feet_to_meters, from_field="GND_ELEV"
        ),
        OneToOneFieldMap(
            to_field="agl", converter=coerce_feet_to_meters, from_field="ANT_HEIGHT"
        ),
        OneToOneFieldMap(to_field="comments", converter=None, from_field="REMARKS"),
    ]
    form_class = PreliminaryFacilityForm
    form_defaults = {"data_source": ACCESS_PRELIM_TECHNICAL}


APPLICANT_FORM_MAP = ApplicantFormMap()
PCASE_FORM_MAP = PcaseFormMap()
PFACILITY_FORM_MAP = PfacilityFormMap()

todo = [
    "REQ_ERP",
    "PATH_AZ",
    "CLASS",
    "NAD27?",
    "NAD83?",
    "FCC4-Point",
    "12-Point",
    "NRAO_DIFF",
    "NRAO_TROPO",
    "NRAO_SPACE",
    "NRAO_TPA",
    "NRAO_AERPD_Analog",
    "NRAO_AERPD_CDMA",
    "NRAO_AZ_GB",
    "TAP_DIFF",
    "TAP_TROPO",
    "TAP_SPACE",
    "TAP_TPA",
    "TAP_AERPD",
    "JSMS_DIFF",
    "JSMS_TROPO",
    "JSMS_SPACE",
    "JSMS_TPA",
    "JSMS_AERPD",
    "PROP_STUDY",
    "PROP_STUDY_Link",
    "MAP",
]
