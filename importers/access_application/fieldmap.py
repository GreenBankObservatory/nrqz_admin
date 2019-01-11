"""Field mappings for Access Application Data"""

import pytz

from django_import_data import FormMap, OneToOneFieldMap, FormMapSet

from cases.forms import AttachmentForm, CaseForm, PersonForm
from importers.converters import (
    coerce_num,
    coerce_positive_int,
    coerce_datetime,
    coerce_bool,
    coerce_path,
)


ACCESS_APPLICATION = "access_application"


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
            to_field="case_num", converter=coerce_positive_int, from_field="NRQZ_NO"
        ),
        OneToOneFieldMap(to_field="comments", converter=None, from_field="COMMENTS"),
        OneToOneFieldMap(
            to_field="original_created_on",
            converter=coerce_datetime,
            from_field="DATEREC",
        ),
        OneToOneFieldMap(
            to_field="original_modified_on",
            converter=coerce_datetime,
            from_field="DATEALTERED",
        ),
        OneToOneFieldMap(
            to_field="completed", converter=coerce_bool, from_field="COMPLETED"
        ),
        OneToOneFieldMap(
            to_field="shutdown", converter=coerce_bool, from_field="SHUTDOWN"
        ),
        OneToOneFieldMap(
            to_field="completed_on", converter=coerce_datetime, from_field="DATECOMP"
        ),
        OneToOneFieldMap(
            to_field="sgrs_notify", converter=coerce_bool, from_field="SGRSNOTIFY"
        ),
        OneToOneFieldMap(
            to_field="sgrs_notified_on",
            converter=coerce_datetime,
            from_field="SGRSDATE",
        ),
        OneToOneFieldMap(
            to_field="radio_service", converter=None, from_field="RADIOSRV"
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
            to_field="erpd_limit", converter=coerce_bool, from_field="ERPD_LIMIT"
        ),
        OneToOneFieldMap(
            to_field="si_waived", converter=coerce_bool, from_field="SIWAIVED"
        ),
        OneToOneFieldMap(to_field="si", converter=coerce_bool, from_field="SI"),
        OneToOneFieldMap(
            to_field="si_done", converter=coerce_datetime, from_field="SIDONE"
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
                OneToOneFieldMap(
                    to_field="path", converter=coerce_path, from_field=f"LETTER{n}_Link"
                )
            ],
            "form_class": AttachmentForm,
            "form_defaults": {
                "data_source": ACCESS_APPLICATION,
                "comments": "Imported by script",
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
