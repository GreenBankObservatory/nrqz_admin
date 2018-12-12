"""Field mappings for Access Preliminary Technical Data"""

from importers.fieldmap import FieldMap
from importers.converters import (
    coerce_scientific_notation,
    coerce_none,
    coerce_feet_to_meters,
)
from importers.access_application.fieldmap import coerce_datetime, coerce_positive_int


applicant_field_mappers = [
    FieldMap(to_field="name", converter=None, from_field="APPLICANT")
]

case_field_mappers = [
    FieldMap(to_field="case_num", converter=coerce_positive_int, from_field="PNRQZ_NO")
]

facility_field_mappers = [
    FieldMap(to_field="site_num", converter=None, from_field="Site Number"),
    FieldMap(
        to_field="original_created_on", converter=coerce_datetime, from_field="DATE"
    ),
    FieldMap(to_field="freq_low", converter=None, from_field="FREQUENCY"),
    FieldMap(to_field="antenna_model_number", converter=None, from_field="ANT_MODEL"),
    FieldMap(
        to_field="power_density_limit",
        converter=coerce_scientific_notation,
        from_field="PWD_LIMIT",
    ),
    FieldMap(to_field="site_name", converter=None, from_field="LOCATION"),
    FieldMap(to_field="latitude", converter=coerce_none, from_field="LATITUDE"),
    FieldMap(to_field="longitude", converter=coerce_none, from_field="LONGITUDE"),
    FieldMap(to_field="amsl", converter=coerce_feet_to_meters, from_field="GND_ELEV"),
    FieldMap(to_field="agl", converter=coerce_feet_to_meters, from_field="ANT_HEIGHT"),
    FieldMap(to_field="comments", converter=None, from_field="REMARKS"),
]

# TODO: Consolidate!
def expand_field_mappers(field_mappers):
    """Generate a map of known_header->importer by "expanding" the from_fields of each FieldMap
    In this way we can easily and efficiently look up a given header and find its associated importer
    """

    field_map = {}
    for importer in field_mappers:
        field_map[importer.from_field] = importer

    return field_map


# TODO: Consolidate!
def get_combined_field_map():
    return expand_field_mappers(
        [*applicant_field_mappers, *case_field_mappers, *facility_field_mappers]
    )


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
