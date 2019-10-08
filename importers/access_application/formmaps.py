"""Field mappings for Access Application Data"""


from django_import_data import FormMap, OneToOneFieldMap, OneToManyFieldMap

from cases.forms import AttachmentImportForm, CaseImportForm, PersonImportForm
from importers.converters import (
    coerce_positive_int,
    convert_access_datetime,
    coerce_bool,
    convert_access_attachment,
    convert_case_num,
    coerce_access_none,
)
from utils.constants import ACCESS_APPLICATION


def convert_radio_service(radio_service):
    clean_radio_service = radio_service.strip().lower()
    is_federal = clean_radio_service in ["gov", "fed", "gvt"]
    return {"radio_service": radio_service, "is_federal": is_federal}


IGNORED_HEADERS = [
    "C_BAND",
    "HF_BAND",
    "KA_BAND",
    "KU_BAND",
    "K_BAND",
    "LETTER1",
    "LETTER2",
    "LETTER3",
    "LETTER4",
    "LETTER5",
    "LETTER6",
    "LETTER7",
    "LETTER8",
    "L_BAND",
    "S_BAND",
    "UHF1_BAND",
    "UHF2_BAND",
    "VHF_BAND",
    "X_BAND",
]


class ApplicantFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            to_field="name", converter=coerce_access_none, from_field="APPLICANT"
        ),
        OneToOneFieldMap(
            to_field="phone", converter=coerce_access_none, from_field="PHONE"
        ),
        OneToOneFieldMap(
            to_field="fax", converter=coerce_access_none, from_field="FAX"
        ),
        OneToOneFieldMap(
            to_field="email", converter=coerce_access_none, from_field="EMAIL"
        ),
        OneToOneFieldMap(
            to_field="street", converter=coerce_access_none, from_field="ADDRESS"
        ),
        OneToOneFieldMap(
            to_field="city", converter=coerce_access_none, from_field="CITY"
        ),
        OneToOneFieldMap(
            to_field="county", converter=coerce_access_none, from_field="COUNTY"
        ),
        OneToOneFieldMap(
            to_field="state", converter=coerce_access_none, from_field="STATE"
        ),
        OneToOneFieldMap(
            to_field="zipcode", converter=coerce_access_none, from_field="ZIPCODE"
        ),
    ]

    form_class = PersonImportForm
    form_defaults = {"data_source": ACCESS_APPLICATION}


class ContactFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            to_field="name", converter=coerce_access_none, from_field="CONTACT"
        )
    ]
    form_class = PersonImportForm
    form_defaults = {"data_source": ACCESS_APPLICATION}


class CaseImportFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            to_field="case_num", converter=convert_case_num, from_field="NRQZ_NO"
        ),
        OneToOneFieldMap(
            to_field="comments", converter=coerce_access_none, from_field="COMMENTS"
        ),
        OneToOneFieldMap(
            to_field="date_received",
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
        OneToOneFieldMap(
            to_field="call_sign", converter=coerce_access_none, from_field="CALLSIGN"
        ),
        OneToOneFieldMap(
            to_field="freq_coord", converter=coerce_access_none, from_field="FCNUMBER"
        ),
        OneToOneFieldMap(
            to_field="fcc_file_num",
            converter=coerce_access_none,
            from_field="FCCNUMBER",
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
            to_field="original_si_done",
            converter=convert_access_datetime,
            from_field="SIDONE",
        ),
    ]

    form_class = CaseImportForm
    form_defaults = {"data_source": ACCESS_APPLICATION}


ATTACHMENT_FORM_MAPS = [
    type(
        "AttachmentImportFormMap",
        (FormMap,),
        {
            "field_maps": [
                OneToManyFieldMap(
                    to_fields=("file_path", "original_index"),
                    converter=convert_access_attachment,
                    from_field=f"LETTER{n}_Link",
                    explanation="This field provides both the letter number and "
                    "the path to the letter",
                )
            ],
            "form_class": AttachmentImportForm,
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
CASE_FORM_MAP = CaseImportFormMap()

# access_application_fms = FormMapSet(form_maps={
#     "applicant": ApplicantFormMap,
#     "contact": ContactFormMap,
#     "case": CaseImportFormMap,
#     **{""}
#     })
