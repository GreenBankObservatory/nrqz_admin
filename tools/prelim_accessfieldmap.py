import pytz

from tools.fieldmap import FieldMap
from .accessfieldmap import (
    coerce_positive_int,
    coerce_bool,
    coerce_path,
    coerce_datetime,
)

applicant_field_mappers = [
    FieldMap(to_field="name", converter=None, from_field="APPLICANT"),
    FieldMap(to_field="phone", converter=None, from_field="PHONE"),
    FieldMap(to_field="fax", converter=None, from_field="FAX"),
    FieldMap(to_field="email", converter=None, from_field="EMAIL"),
    FieldMap(to_field="street", converter=None, from_field="ADDRESS"),
    FieldMap(to_field="city", converter=None, from_field="CITY"),
    FieldMap(to_field="county", converter=None, from_field="COUNTY"),
    FieldMap(to_field="state", converter=None, from_field="STATE"),
    FieldMap(to_field="zipcode", converter=None, from_field="ZIPCODE"),
]

contact_field_mappers = [
    FieldMap(to_field="name", converter=None, from_field="CONTACT")
]

case_field_mappers = [
    FieldMap(to_field="case_num", converter=coerce_positive_int, from_field="PNRQZ_NO"),
    FieldMap(to_field="comments", converter=None, from_field="COMMENTS"),
    FieldMap(to_field="created_on", converter=coerce_datetime, from_field="DATEREC"),
    FieldMap(to_field="completed", converter=coerce_bool, from_field="COMPLETED"),
    FieldMap(to_field="completed_on", converter=coerce_datetime, from_field="DATECOMP"),
    FieldMap(to_field="radio_service", converter=None, from_field="RADIOSRV"),
    FieldMap(
        to_field="num_freqs", converter=coerce_positive_int, from_field="NO_FREQS"
    ),
    FieldMap(
        to_field="num_sites", converter=coerce_positive_int, from_field="NO_SITES"
    ),
    FieldMap(to_field="letter1", converter=coerce_path, from_field="LETTER1_Link"),
    FieldMap(to_field="letter2", converter=coerce_path, from_field="LETTER2_Link"),
    FieldMap(to_field="letter3", converter=coerce_path, from_field="LETTER3_Link"),
]


def expand_field_mappers(field_mappers):
    """Generate a map of known_header->importer by "expanding" the from_fields of each FieldMap
    In this way we can easily and efficiently look up a given header and find its associated importer
    """

    field_map = {}
    for importer in field_mappers:
        field_map[importer.from_field] = importer

    return field_map


def get_combined_field_map():
    return expand_field_mappers(
        [*applicant_field_mappers, *contact_field_mappers, *case_field_mappers]
    )


def print_field_map(field_map):
    """Print out a simple report of the final header->field mappings"""

    # from_field_len is just the longest header in the map plus some padding
    from_field_len = max(len(from_field) for from_field in field_map) + 3
    for from_field, importer in field_map.items():
        print(f"{from_field!r:{from_field_len}}: {importer.to_field!r}")


if __name__ == "__main__":
    print("Case field map:")
    print_field_map(expand_field_mappers(case_field_mappers))
    print()
    print("Person field map:")
    print_field_map(expand_field_mappers(applicant_field_mappers))
