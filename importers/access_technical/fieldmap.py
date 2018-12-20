"""Field mappings for Access Technical Data"""

from cases.forms import CaseForm, FacilityForm, PersonForm

from importers.fieldmap import FormMap, FieldMap
from importers.access_application.fieldmap import coerce_datetime, coerce_positive_int
from importers.converters import (
    coerce_scientific_notation,
    coerce_none,
    coerce_feet_to_meters,
)


ACCESS_TECHNICAL = "access_technical"

CASE_FORM_MAP = FormMap(
    field_maps=[
        FieldMap(
            to_field="case_num", converter=coerce_positive_int, from_field="NRQZ_NO"
        )
    ],
    form_class=CaseForm,
    form_defaults={"data_source": ACCESS_TECHNICAL},
)

APPLICANT_FORM_MAP = FormMap(
    field_maps=[FieldMap(to_field="name", converter=None, from_field="APPLICANT")],
    form_class=PersonForm,
    form_defaults={"data_source": ACCESS_TECHNICAL},
)

FACILITY_FORM_MAP = FormMap(
    field_maps=[
        FieldMap(
            to_field="antenna_model_number", converter=None, from_field="ANT_MODEL"
        ),
        FieldMap(
            to_field="original_created_on",
            converter=coerce_datetime,
            from_field="DATEREC",
        ),
        FieldMap(to_field="call_sign", converter=None, from_field="CALLSIGN"),
        FieldMap(to_field="freq_low", converter=None, from_field="FREQUENCY"),
        FieldMap(
            to_field="power_density_limit",
            converter=coerce_scientific_notation,
            from_field="PWD_LIMIT",
        ),
        FieldMap(
            to_field="site_num", converter=coerce_positive_int, from_field="SITE."
        ),
        # TODO: hmmmm
        FieldMap(to_field="site_name", converter=None, from_field="LOCATION"),
        FieldMap(to_field="latitude", converter=coerce_none, from_field="LATITUDE"),
        FieldMap(to_field="longitude", converter=coerce_none, from_field="LONGITUDE"),
        FieldMap(
            to_field="amsl", converter=coerce_feet_to_meters, from_field="GND_ELEV"
        ),
        FieldMap(
            to_field="agl", converter=coerce_feet_to_meters, from_field="ANT_HEIGHT"
        ),
        FieldMap(to_field="comments", converter=None, from_field="REMARKS"),
    ],
    form_class=FacilityForm,
    form_defaults={"data_source": ACCESS_TECHNICAL},
)
