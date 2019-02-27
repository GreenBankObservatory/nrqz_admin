"""Field mappings for Access Technical Data"""

from cases.forms import AttachmentForm, CaseForm, FacilityImportForm, PersonForm

from django_import_data import FormMap, ManyToOneFieldMap, OneToOneFieldMap
from importers.access_application.fieldmap import (
    convert_access_datetime,
    coerce_positive_int,
)
from importers.converters import (
    coerce_access_location,
    coerce_bool,
    coerce_feet_to_meters,
    coerce_none,
    coerce_positive_float,
    coerce_scientific_notation,
    convert_access_path,
    convert_array,
    convert_case_num,
    convert_case_num_and_site_num_to_nrqz_id,
)
from utils.constants import ACCESS_TECHNICAL

IGNORED_HEADERS = ["QZPATHLOSS", "MAP", "DATEREC"]


class CaseFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            to_field="case_num", converter=convert_case_num, from_field="NRQZ_NO"
        ),
        OneToOneFieldMap(
            to_field="agency_num", converter=coerce_none, from_field="AGENCY_NO"
        ),
    ]
    form_class = CaseForm
    form_defaults = {"data_source": ACCESS_TECHNICAL}


class ApplicantFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(to_field="name", converter=None, from_field="APPLICANT")
    ]
    form_class = PersonForm
    form_defaults = {"data_source": ACCESS_TECHNICAL}


class FacilityFormMap(FormMap):
    field_maps = [
        ManyToOneFieldMap(
            from_fields={"case_num": "NRQZ_NO", "site_num": "Site Number"},
            converter=convert_case_num_and_site_num_to_nrqz_id,
            to_field="nrqz_id",
        ),
        OneToOneFieldMap(
            to_field="meets_erpd_limit", converter=coerce_bool, from_field="ERP_LIMIT"
        ),
        OneToOneFieldMap(
            to_field="antenna_model_number", converter=None, from_field="ANT_MODEL"
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
        OneToOneFieldMap(to_field="s367", converter=coerce_bool, from_field="S367"),
        ManyToOneFieldMap(
            to_field="emissions",
            converter=convert_array,
            from_fields=("EMISSION", "EMISSION1", "EMISSION2"),
        ),
        OneToOneFieldMap(
            to_field="radio_service", converter=coerce_none, from_field="CLASS"
        ),
        OneToOneFieldMap(
            from_field="4_Point", converter=coerce_bool, to_field="topo_4_point"
        ),
        OneToOneFieldMap(
            from_field="12_Point", converter=coerce_bool, to_field="topo_12_point"
        ),
        OneToOneFieldMap(
            to_field="az_bearing",
            converter=coerce_positive_float,
            from_field="NRAO_AZ_GB",
        ),
        OneToOneFieldMap(
            to_field="tpa", converter=coerce_positive_float, from_field="NRAO_TPA"
        ),
        OneToOneFieldMap(
            to_field="requested_max_erp_per_tx",
            converter=coerce_positive_float,
            from_field="REQ_ERP",
        ),
        OneToOneFieldMap(from_field="1A", converter=coerce_bool, to_field="survey_1a"),
        OneToOneFieldMap(from_field="2C", converter=coerce_bool, to_field="survey_2c"),
        OneToOneFieldMap(
            from_field="NRAO-AERPD-CDMA2000",
            converter=coerce_positive_float,
            to_field="nrao_aerpd_cdma2000",
        ),
        OneToOneFieldMap(
            from_field="NRAO-AERPD-GSM",
            converter=coerce_positive_float,
            to_field="nrao_aerpd_gsm",
        ),
        OneToOneFieldMap(
            from_field="NRAO_AERPD_Emission",
            converter=coerce_positive_float,
            to_field="nrao_aerpd",
        ),
        OneToOneFieldMap(
            from_field="NRAO-AERPD-CDMA",
            converter=coerce_positive_float,
            to_field="nrao_aerpd_cdma",
        ),
        OneToOneFieldMap(
            from_field="NRAO_AERPD_Analog",
            converter=coerce_positive_float,
            to_field="nrao_aerpd_analog",
        ),
        OneToOneFieldMap(
            from_field="NRAO_DIFF",
            converter=coerce_positive_float,
            to_field="nrao_diff",
        ),
        OneToOneFieldMap(
            from_field="NRAO_SPACE",
            converter=coerce_positive_float,
            to_field="nrao_space",
        ),
        OneToOneFieldMap(
            from_field="NRAO_TROPO",
            converter=coerce_positive_float,
            to_field="nrao_tropo",
        ),
        OneToOneFieldMap(
            from_field="OUTSIDE",
            converter=coerce_bool,
            to_field="original_outside_nrqz",
        ),
    ]
    form_class = FacilityImportForm
    form_defaults = {"data_source": ACCESS_TECHNICAL}


class PropagationStudyFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            to_field="path",
            converter=convert_access_path,
            from_field=f"QZPATHLOSS_Link",
        )
    ]
    form_class = AttachmentForm
    form_defaults = {"data_source": ACCESS_TECHNICAL, "comments": "Propagation Study"}


APPLICANT_FORM_MAP = ApplicantFormMap()
CASE_FORM_MAP = CaseFormMap()
FACILITY_FORM_MAP = FacilityFormMap()
PROPAGATION_STUDY_FORM_MAP = PropagationStudyFormMap()
