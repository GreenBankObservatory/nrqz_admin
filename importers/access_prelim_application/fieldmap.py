"""Field mappings for Access Preliminary Application Data"""

from cases.forms import AttachmentForm, PersonForm, PreliminaryCaseForm

from importers.fieldmap import FormMap, FieldMap
from importers.access_application.fieldmap import (
    coerce_positive_int,
    coerce_bool,
    coerce_path,
    coerce_datetime,
)
from utils.constants import ACCESS_PRELIM_APPLICATION

APPLICANT_FORM_MAP = FormMap(
    field_maps=[
        FieldMap(to_field="name", converter=None, from_field="APPLICANT"),
        FieldMap(to_field="phone", converter=None, from_field="PHONE"),
        FieldMap(to_field="fax", converter=None, from_field="FAX"),
        FieldMap(to_field="email", converter=None, from_field="EMAIL"),
        FieldMap(to_field="street", converter=None, from_field="ADDRESS"),
        FieldMap(to_field="city", converter=None, from_field="CITY"),
        FieldMap(to_field="county", converter=None, from_field="COUNTY"),
        FieldMap(to_field="state", converter=None, from_field="STATE"),
        FieldMap(to_field="zipcode", converter=None, from_field="ZIPCODE"),
    ],
    form_class=PersonForm,
    form_defaults={"data_source": ACCESS_PRELIM_APPLICATION},
)

CONTACT_FORM_MAP = FormMap(
    field_maps=[FieldMap(to_field="name", converter=None, from_field="CONTACT")],
    form_class=PersonForm,
    form_defaults={"data_source": ACCESS_PRELIM_APPLICATION},
)

PCASE_FORM_MAP = FormMap(
    field_maps=[
        FieldMap(
            to_field="case_num", converter=coerce_positive_int, from_field="PNRQZ_NO"
        ),
        FieldMap(to_field="comments", converter=None, from_field="COMMENTS"),
        FieldMap(
            to_field="original_created_on",
            converter=coerce_datetime,
            from_field="DATEREC",
        ),
        FieldMap(to_field="completed", converter=coerce_bool, from_field="COMPLETED"),
        FieldMap(
            to_field="completed_on", converter=coerce_datetime, from_field="DATECOMP"
        ),
        FieldMap(to_field="radio_service", converter=None, from_field="RADIOSRV"),
        FieldMap(
            to_field="num_freqs", converter=coerce_positive_int, from_field="NO_FREQS"
        ),
        FieldMap(
            to_field="num_sites", converter=coerce_positive_int, from_field="NO_SITES"
        ),
    ],
    form_class=PreliminaryCaseForm,
    form_defaults={"data_source": ACCESS_PRELIM_APPLICATION},
)

ATTACHMENT_FORM_MAPS = [
    FormMap(
        field_maps=[
            FieldMap(
                to_field="path", converter=coerce_path, from_field=f"LETTER{n}_Link"
            )
        ],
        form_class=AttachmentForm,
    )
    for n in range(1, 3)
]
