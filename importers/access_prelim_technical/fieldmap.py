"""Field mappings for Access Preliminary Technical Data"""
from cases.forms import PersonForm, PreliminaryCaseForm, PreliminaryFacilityForm

from importers.fieldmap import FieldMap, FormMap
from importers.converters import (
    coerce_scientific_notation,
    coerce_none,
    coerce_feet_to_meters,
    coerce_location,
)
from importers.access_application.fieldmap import coerce_datetime, coerce_positive_int

ACCESS_PRELIM_TECHNICAL = "access_prelim_technical"

APPLICANT_FORM_MAP = FormMap(
    field_maps=[FieldMap(to_field="name", converter=None, from_field="APPLICANT")],
    form_class=PersonForm,
    form_defaults={"data_source": ACCESS_PRELIM_TECHNICAL},
)

PCASE_FORM_MAP = FormMap(
    field_maps=[
        FieldMap(
            to_field="case_num", converter=coerce_positive_int, from_field="PNRQZ_NO"
        )
    ],
    form_class=PreliminaryCaseForm,
    form_defaults={"data_source": ACCESS_PRELIM_TECHNICAL},
)

PFACILITY_FORM_MAP = FormMap(
    field_maps=[
        FieldMap(to_field="site_num", converter=None, from_field="Site Number"),
        FieldMap(
            to_field="original_created_on", converter=coerce_datetime, from_field="DATE"
        ),
        FieldMap(to_field="freq_low", converter=None, from_field="FREQUENCY"),
        FieldMap(
            to_field="antenna_model_number", converter=None, from_field="ANT_MODEL"
        ),
        FieldMap(
            to_field="power_density_limit",
            converter=coerce_scientific_notation,
            from_field="PWD_LIMIT",
        ),
        FieldMap(to_field="site_name", converter=None, from_field="LOCATION"),
        FieldMap(to_field="latitude", converter=coerce_none, from_field="LATITUDE"),
        FieldMap(to_field="longitude", converter=coerce_none, from_field="LONGITUDE"),
        FieldMap(
            to_field="location",
            converter=coerce_location,
            from_fields=({"latitude": ("LATITUDE",), "longitude": ("LONGITUDE",)}),
        ),
        FieldMap(
            to_field="amsl", converter=coerce_feet_to_meters, from_field="GND_ELEV"
        ),
        FieldMap(
            to_field="agl", converter=coerce_feet_to_meters, from_field="ANT_HEIGHT"
        ),
        FieldMap(to_field="comments", converter=None, from_field="REMARKS"),
    ],
    form_class=PreliminaryFacilityForm,
    form_defaults={"data_source": ACCESS_PRELIM_TECHNICAL},
)


print(f"APPLICANT_FORM_MAP:\n{APPLICANT_FORM_MAP}\n---\n")
print(f"PCASE_FORM_MAP:\n{PCASE_FORM_MAP}\n---\n")
print(f"PFACILITY_FORM_MAP:\n{PFACILITY_FORM_MAP}\n---\n")

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
