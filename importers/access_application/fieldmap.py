"""Field mappings for Access Application Data"""

from datetime import datetime
import pytz

from cases.forms import AttachmentForm, CaseForm, PersonForm
from importers.fieldmap import FormMap, FieldMap
from importers.converters import (
    coerce_num,
    coerce_positive_int,
    coerce_datetime,
    coerce_bool,
    coerce_path,
)


ACCESS_APPLICATION = "access_application"

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
    form_defaults={"data_source": ACCESS_APPLICATION},
)

CONTACT_FORM_MAP = FormMap(
    field_maps=[FieldMap(to_field="name", converter=None, from_field="CONTACT")],
    form_class=PersonForm,
    form_defaults={"data_source": ACCESS_APPLICATION},
)


CASE_FORM_MAP = FormMap(
    field_maps=[
        FieldMap(
            to_field="case_num", converter=coerce_positive_int, from_field="NRQZ_NO"
        ),
        FieldMap(to_field="comments", converter=None, from_field="COMMENTS"),
        FieldMap(
            to_field="original_created_on",
            converter=coerce_datetime,
            from_field="DATEREC",
        ),
        FieldMap(
            to_field="original_modified_on",
            converter=coerce_datetime,
            from_field="DATEALTERED",
        ),
        FieldMap(to_field="completed", converter=coerce_bool, from_field="COMPLETED"),
        FieldMap(to_field="shutdown", converter=coerce_bool, from_field="SHUTDOWN"),
        FieldMap(
            to_field="completed_on", converter=coerce_datetime, from_field="DATECOMP"
        ),
        FieldMap(
            to_field="sgrs_notify", converter=coerce_bool, from_field="SGRSNOTIFY"
        ),
        FieldMap(
            to_field="sgrs_notified_on",
            converter=coerce_datetime,
            from_field="SGRSDATE",
        ),
        FieldMap(to_field="radio_service", converter=None, from_field="RADIOSRV"),
        FieldMap(to_field="call_sign", converter=None, from_field="CALLSIGN"),
        FieldMap(to_field="freq_coord", converter=None, from_field="FCNUMBER"),
        FieldMap(to_field="fcc_file_num", converter=None, from_field="FCCNUMBER"),
        FieldMap(
            to_field="num_freqs", converter=coerce_positive_int, from_field="NO_FREQS"
        ),
        FieldMap(
            to_field="num_sites", converter=coerce_positive_int, from_field="NO_SITES"
        ),
        FieldMap(
            to_field="num_outside",
            converter=coerce_positive_int,
            from_field="NO_OUTSIDE",
        ),
        FieldMap(to_field="erpd_limit", converter=coerce_bool, from_field="ERPD_LIMIT"),
        FieldMap(to_field="si_waived", converter=coerce_bool, from_field="SIWAIVED"),
        FieldMap(to_field="si", converter=coerce_bool, from_field="SI"),
        FieldMap(to_field="si_done", converter=coerce_datetime, from_field="SIDONE"),
    ],
    form_class=CaseForm,
    form_defaults={"data_source": ACCESS_APPLICATION},
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
    for n in range(1, 9)
]
