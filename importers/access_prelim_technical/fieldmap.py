"""Field mappings for Access Preliminary Technical Data"""
from cases.forms import (
    AttachmentForm,
    PersonForm,
    PreliminaryCaseForm,
    PreliminaryFacilityImportForm,
)

from django_import_data import OneToOneFieldMap, ManyToOneFieldMap, FormMap
from importers.converters import (
    convert_access_datetime,
    coerce_feet_to_meters,
    coerce_access_location,
    coerce_none,
    coerce_positive_float,
    coerce_positive_int,
    coerce_scientific_notation,
    convert_access_path,
    convert_case_num,
)
from utils.constants import ACCESS_PRELIM_TECHNICAL


class ApplicantFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(to_field="name", converter=None, from_field="APPLICANT")
    ]
    form_class = PersonForm
    form_defaults = {"data_source": ACCESS_PRELIM_TECHNICAL}


class PcaseFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            to_field="case_num", converter=convert_case_num, from_field="PNRQZ_NO"
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
            to_field="original_created_on",
            converter=convert_access_datetime,
            from_field="DATE",
        ),
        OneToOneFieldMap(
            to_field="freq_low", converter=coerce_positive_float, from_field="FREQUENCY"
        ),
        OneToOneFieldMap(
            to_field="antenna_model_number", converter=None, from_field="ANT_MODEL"
        ),
        OneToOneFieldMap(
            to_field="power_density_limit",
            converter=coerce_scientific_notation,
            from_field="PWD_LIMIT",
        ),
        OneToOneFieldMap(
            to_field="location_description", converter=None, from_field="LOCATION"
        ),
        OneToOneFieldMap(
            to_field="latitude", converter=coerce_none, from_field="LATITUDE"
        ),
        OneToOneFieldMap(
            to_field="longitude", converter=coerce_none, from_field="LONGITUDE"
        ),
        ManyToOneFieldMap(
            to_field="location",
            converter=coerce_access_location,
            from_fields=(
                {
                    "latitude": "LATITUDE",
                    "longitude": "LONGITUDE",
                    "nad27": "NAD27?",
                    "nad83": "NAD83?",
                }
            ),
        ),
        OneToOneFieldMap(
            to_field="amsl", converter=coerce_feet_to_meters, from_field="GND_ELEV"
        ),
        OneToOneFieldMap(
            to_field="agl", converter=coerce_feet_to_meters, from_field="ANT_HEIGHT"
        ),
        OneToOneFieldMap(to_field="comments", converter=None, from_field="REMARKS"),
        OneToOneFieldMap(to_field="tpa", converter=None, from_field="NRAO_TPA"),
        # OneToOneFieldMap(to_field="weighted_12_point", converter=None, from_field="12-Point"),
    ]
    form_class = PreliminaryFacilityImportForm
    form_defaults = {"data_source": ACCESS_PRELIM_TECHNICAL}


class AttachmentFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            to_field="path",
            converter=convert_access_path,
            from_field=f"PROP_STUDY_Link",
        )
    ]
    form_class = AttachmentForm
    form_defaults = {
        "data_source": ACCESS_PRELIM_TECHNICAL,
        "comments": "Propagation Study",
    }


APPLICANT_FORM_MAP = ApplicantFormMap()
PCASE_FORM_MAP = PcaseFormMap()
PFACILITY_FORM_MAP = PfacilityFormMap()
ATTACHMENT_FORM_MAP = AttachmentFormMap()

todo = [
    "REQ_ERP",
    "PATH_AZ",
    "CLASS",
    "FCC4-Point",
    "NRAO_DIFF",
    "NRAO_TROPO",
    "NRAO_SPACE",
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
    "MAP",
]
