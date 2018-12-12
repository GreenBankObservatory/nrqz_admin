"""Field mappings for Access Technical Data"""

from importers.fieldmap import FieldMap
from importers.access_application.fieldmap import coerce_datetime, coerce_positive_int
from importers.converters import (
    coerce_scientific_notation,
    coerce_none,
    coerce_feet_to_meters,
)


applicant_field_mappers = [
    FieldMap(to_field="name", converter=None, from_field="APPLICANT")
]

facility_field_mappers = [
    FieldMap(to_field="case_num", converter=coerce_positive_int, from_field="NRQZ_NO"),
    FieldMap(to_field="antenna_model_number", converter=None, from_field="ANT_MODEL"),
    FieldMap(
        to_field="original_created_on", converter=coerce_datetime, from_field="DATEREC"
    ),
    FieldMap(to_field="call_sign", converter=None, from_field="CALLSIGN"),
    FieldMap(to_field="freq_low", converter=None, from_field="FREQUENCY"),
    FieldMap(
        to_field="power_density_limit",
        converter=coerce_scientific_notation,
        from_field="PWD_LIMIT",
    ),
    FieldMap(to_field="site_num", converter=coerce_positive_int, from_field="SITE."),
    # TODO: hmmmm
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
    return expand_field_mappers([*applicant_field_mappers, *facility_field_mappers])


def print_field_map(field_map):
    """Print out a simple report of the final header->field mappings"""

    # from_field_len is just the longest header in the map plus some padding
    from_field_len = max(len(from_field) for from_field in field_map) + 3
    for from_field, importer in field_map.items():
        print(f"{from_field!r:{from_field_len}}: {importer.to_field!r}")
