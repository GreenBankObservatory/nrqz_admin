"""Field mappings for Access Technical Data"""

from cases.forms import AttachmentForm, CaseForm, FacilityForm, PersonForm

from django_import_data import FormMap, ManyToOneFieldMap, OneToOneFieldMap
from importers.access_application.fieldmap import coerce_datetime, coerce_positive_int
from importers.converters import (
    coerce_feet_to_meters,
    coerce_access_location,
    coerce_none,
    coerce_positive_float,
    coerce_scientific_notation,
    convert_access_path,
    convert_case_num,
)
from utils.constants import ACCESS_TECHNICAL


class CaseFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            to_field="case_num", converter=convert_case_num, from_field="NRQZ_NO"
        )
    ]
    form_class = CaseForm
    form_defaults = {"data_source": ACCESS_TECHNICAL}


CASE_FORM_MAP = CaseFormMap()


class ApplicantFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(to_field="name", converter=None, from_field="APPLICANT")
    ]
    form_class = PersonForm
    form_defaults = {"data_source": ACCESS_TECHNICAL}


APPLICANT_FORM_MAP = ApplicantFormMap()


class FacilityFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            to_field="antenna_model_number", converter=None, from_field="ANT_MODEL"
        ),
        OneToOneFieldMap(
            to_field="original_created_on",
            converter=coerce_datetime,
            from_field="DATEREC",
        ),
        OneToOneFieldMap(to_field="call_sign", converter=None, from_field="CALLSIGN"),
        OneToOneFieldMap(
            to_field="freq_low", converter=coerce_positive_float, from_field="FREQUENCY"
        ),
        OneToOneFieldMap(
            to_field="power_density_limit",
            converter=coerce_scientific_notation,
            from_field="PWD_LIMIT",
        ),
        OneToOneFieldMap(
            to_field="site_num", converter=coerce_positive_int, from_field="SITE."
        ),
        # TODO: hmmmm
        OneToOneFieldMap(to_field="site_name", converter=None, from_field="LOCATION"),
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
                    "nad83": "NAD82?",
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
    ]
    form_class = FacilityForm
    form_defaults = {"data_source": ACCESS_TECHNICAL}


class AttachmentFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            to_field="path",
            converter=convert_access_path,
            from_field=f"QZPATHLOSS_Link",
        )
    ]
    form_class = AttachmentForm
    form_defaults = {"data_source": ACCESS_TECHNICAL, "comments": "QZ Path Loss"}


FACILITY_FORM_MAP = FacilityFormMap()
ATTACHMENT_FORM_MAP = AttachmentFormMap()
