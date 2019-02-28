"""Field mappings for Access Application Data"""

import pytz

from django_import_data import FormMap, OneToOneFieldMap, OneToManyFieldMap

from cases.forms import AttachmentForm, CaseForm, PersonForm
from importers.converters import (
    coerce_float,
    coerce_positive_int,
    convert_access_datetime,
    coerce_bool,
    convert_access_attachment,
    convert_case_num,
)
from utils.constants import ACCESS_APPLICATION


def convert_radio_service(radio_service):
    clean_radio_service = radio_service.strip().lower()
    is_federal = clean_radio_service in ["gov", "fed", "gvt"]
    return {"radio_service": radio_service, "is_federal": is_federal}


class ApplicantFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(to_field="name", converter=None, from_field="APPLICANT"),
        OneToOneFieldMap(to_field="phone", converter=None, from_field="PHONE"),
        OneToOneFieldMap(to_field="fax", converter=None, from_field="FAX"),
        OneToOneFieldMap(to_field="email", converter=None, from_field="EMAIL"),
        OneToOneFieldMap(to_field="street", converter=None, from_field="ADDRESS"),
        OneToOneFieldMap(to_field="city", converter=None, from_field="CITY"),
        OneToOneFieldMap(to_field="county", converter=None, from_field="COUNTY"),
        OneToOneFieldMap(to_field="state", converter=None, from_field="STATE"),
        OneToOneFieldMap(to_field="zipcode", converter=None, from_field="ZIPCODE"),
    ]

    form_class = PersonForm
    form_defaults = {"data_source": ACCESS_APPLICATION}


class ContactFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(to_field="name", converter=None, from_field="CONTACT")
    ]
    form_class = PersonForm
    form_defaults = {"data_source": ACCESS_APPLICATION}


class CaseFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            to_field="case_num", converter=convert_case_num, from_field="NRQZ_NO"
        ),
        OneToOneFieldMap(to_field="comments", converter=None, from_field="COMMENTS"),
        OneToOneFieldMap(
            to_field="date_recorded",
            converter=convert_access_datetime,
            from_field="DATEREC",
        ),
        OneToOneFieldMap(
            to_field="original_modified_on",
            converter=convert_access_datetime,
            from_field="DATEALTERED",
        ),
        OneToOneFieldMap(
            to_field="completed", converter=coerce_bool, from_field="COMPLETED"
        ),
        OneToOneFieldMap(
            to_field="shutdown", converter=coerce_bool, from_field="SHUTDOWN"
        ),
        OneToOneFieldMap(
            to_field="completed_on",
            converter=convert_access_datetime,
            from_field="DATECOMP",
        ),
        OneToOneFieldMap(
            to_field="sgrs_notify", converter=coerce_bool, from_field="SGRSNOTIFY"
        ),
        OneToOneFieldMap(
            to_field="sgrs_responded_on",
            converter=convert_access_datetime,
            from_field="SGRSDATE",
        ),
        OneToManyFieldMap(
            to_fields=("radio_service", "is_federal"),
            converter=convert_radio_service,
            from_field={"radio_service": "RADIOSRV"},
        ),
        OneToOneFieldMap(to_field="call_sign", converter=None, from_field="CALLSIGN"),
        OneToOneFieldMap(to_field="freq_coord", converter=None, from_field="FCNUMBER"),
        OneToOneFieldMap(
            to_field="fcc_file_num", converter=None, from_field="FCCNUMBER"
        ),
        OneToOneFieldMap(
            to_field="num_freqs", converter=coerce_positive_int, from_field="NO_FREQS"
        ),
        OneToOneFieldMap(
            to_field="num_sites", converter=coerce_positive_int, from_field="NO_SITES"
        ),
        OneToOneFieldMap(
            to_field="num_outside",
            converter=coerce_positive_int,
            from_field="NO_OUTSIDE",
        ),
        OneToOneFieldMap(
            to_field="original_meets_erpd_limit",
            converter=coerce_bool,
            from_field="ERPD_LIMIT",
        ),
        OneToOneFieldMap(
            to_field="si_waived", converter=coerce_bool, from_field="SIWAIVED"
        ),
        OneToOneFieldMap(to_field="si", converter=coerce_bool, from_field="SI"),
        OneToOneFieldMap(
            to_field="si_done", converter=convert_access_datetime, from_field="SIDONE"
        ),
    ]

    form_class = CaseForm
    form_defaults = {"data_source": ACCESS_APPLICATION}


ATTACHMENT_FORM_MAPS = [
    type(
        "AttachmentFormMap",
        (FormMap,),
        {
            "field_maps": [
                OneToManyFieldMap(
                    to_fields=("path", "original_index"),
                    converter=convert_access_attachment,
                    from_field=f"LETTER{n}_Link",
                    explanation="This field provides both the letter number and "
                    "the path to the letter",
                )
            ],
            "form_class": AttachmentForm,
            "form_defaults": {
                "data_source": ACCESS_APPLICATION,
                "comments": f"Letter {n}",
            },
        },
    )()
    for n in range(1, 9)
]

APPLICANT_FORM_MAP = ApplicantFormMap()
CONTACT_FORM_MAP = ContactFormMap()
CASE_FORM_MAP = CaseFormMap()

# access_application_fms = FormMapSet(form_maps={
#     "applicant": ApplicantFormMap,
#     "contact": ContactFormMap,
#     "case": CaseFormMap,
#     **{""}
#     })
