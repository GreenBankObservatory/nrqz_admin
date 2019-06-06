"""Field mappings for Access Preliminary Technical Data"""
from cases.forms import (
    AttachmentImportForm,
    PersonImportForm,
    PreliminaryCaseImportForm,
    PreliminaryFacilityImportForm,
)

from django_import_data import OneToOneFieldMap, ManyToOneFieldMap, FormMap

from importers.converters import (
    coerce_feet_to_meters,
    coerce_access_location,
    coerce_none,
    coerce_positive_float,
    coerce_positive_int,
    coerce_scientific_notation,
    convert_access_path,
    convert_case_num,
    convert_case_num_and_site_num_to_nrqz_id,
    coerce_bool,
    coerce_access_none,
)
from utils.constants import ACCESS_PRELIM_TECHNICAL

IGNORED_HEADERS = [
    "PROP_STUDY",
    "JSMS_DIFF",
    "JSMS_TROPO",
    "JSMS_SPACE",
    "JSMS_TPA",
    "JSMS_AERPD",
    "TAP_DIFF",
    "TAP_TROPO",
    "TAP_SPACE",
    "TAP_AERPD",
    "TAP_TPA",
    "MAP",
    "DATE",
]


class ApplicantFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(to_field="name", converter=None, from_field="APPLICANT")
    ]
    form_class = PersonImportForm
    form_defaults = {"data_source": ACCESS_PRELIM_TECHNICAL}


class PCaseImportFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            to_field="case_num", converter=convert_case_num, from_field="PNRQZ_NO"
        )
    ]
    form_class = PreliminaryCaseImportForm
    form_defaults = {"data_source": ACCESS_PRELIM_TECHNICAL}


class PFacilityImportFormMap(FormMap):
    field_maps = [
        ManyToOneFieldMap(
            from_fields={"case_num": "PNRQZ_NO", "site_num": "Site Number"},
            converter=convert_case_num_and_site_num_to_nrqz_id,
            to_field="nrqz_id",
        ),
        OneToOneFieldMap(
            to_field="site_num", converter=coerce_positive_int, from_field="Site Number"
        ),
        OneToOneFieldMap(
            to_field="freq_low", converter=coerce_positive_float, from_field="FREQUENCY"
        ),
        OneToOneFieldMap(
            to_field="antenna_model_number",
            converter=coerce_access_none,
            from_field="ANT_MODEL",
        ),
        OneToOneFieldMap(
            to_field="power_density_limit",
            converter=coerce_scientific_notation,
            from_field="PWD_LIMIT",
        ),
        OneToOneFieldMap(
            to_field="location_description",
            converter=coerce_access_none,
            from_field="LOCATION",
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
        OneToOneFieldMap(
            to_field="comments", converter=coerce_access_none, from_field="REMARKS"
        ),
        OneToOneFieldMap(
            to_field="tpa", converter=coerce_positive_float, from_field="NRAO_TPA"
        ),
        OneToOneFieldMap(
            to_field="radio_service", converter=coerce_none, from_field="CLASS"
        ),
        OneToOneFieldMap(
            from_field={"topo_4_point": "FCC4-Point"},
            converter=coerce_bool,
            to_field="topo_4_point",
        ),
        OneToOneFieldMap(
            from_field={"topo_12_point": "12-Point"},
            converter=coerce_bool,
            to_field="topo_12_point",
        ),
        OneToOneFieldMap(
            from_field="NRAO_AZ_GB",
            converter=coerce_positive_float,
            to_field="az_bearing",
        ),
        OneToOneFieldMap(
            from_field="REQ_ERP",
            converter=coerce_positive_float,
            to_field="requested_max_erp_per_tx",
        ),
        OneToOneFieldMap(
            from_field="NRAO_AERPD_CDMA",
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
    form_class = PreliminaryFacilityImportForm
    form_defaults = {"data_source": ACCESS_PRELIM_TECHNICAL}


# PROP STUDY
class PropagationStudyFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            to_field="path",
            converter=convert_access_path,
            from_field=f"PROP_STUDY_Link",
        )
    ]
    form_class = AttachmentImportForm
    form_defaults = {
        "data_source": ACCESS_PRELIM_TECHNICAL,
        "comments": "Propagation Study",
    }


APPLICANT_FORM_MAP = ApplicantFormMap()
PCASE_FORM_MAP = PCaseImportFormMap()
PFACILITY_FORM_MAP = PFacilityImportFormMap()
PROPAGATION_STUDY_FORM_MAP = PropagationStudyFormMap()
