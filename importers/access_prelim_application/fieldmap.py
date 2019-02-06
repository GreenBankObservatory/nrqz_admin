"""Field mappings for Access Preliminary Application Data"""

from cases.forms import AttachmentForm, PersonForm, PreliminaryCaseForm

from django_import_data import FormMap, OneToOneFieldMap, OneToManyFieldMap
from importers.converters import (
    coerce_positive_int,
    coerce_bool,
    convert_access_attachment,
    coerce_datetime,
    convert_case_num,
)
from utils.constants import ACCESS_PRELIM_APPLICATION


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
    form_defaults = {"data_source": ACCESS_PRELIM_APPLICATION}


APPLICANT_FORM_MAP = ApplicantFormMap()


class ContactFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(to_field="name", converter=None, from_field="CONTACT")
    ]
    form_class = PersonForm
    form_defaults = {"data_source": ACCESS_PRELIM_APPLICATION}


CONTACT_FORM_MAP = ContactFormMap()


class PcaseFormMap(FormMap):
    field_maps = [
        OneToOneFieldMap(
            to_field="case_num", converter=convert_case_num, from_field="PNRQZ_NO"
        ),
        OneToOneFieldMap(to_field="comments", converter=None, from_field="COMMENTS"),
        OneToOneFieldMap(
            to_field="original_created_on",
            converter=coerce_datetime,
            from_field="DATEREC",
        ),
        OneToOneFieldMap(
            to_field="completed", converter=coerce_bool, from_field="COMPLETED"
        ),
        OneToOneFieldMap(
            to_field="completed_on", converter=coerce_datetime, from_field="DATECOMP"
        ),
        OneToOneFieldMap(
            to_field="radio_service", converter=None, from_field="RADIOSRV"
        ),
        OneToOneFieldMap(
            to_field="num_freqs", converter=coerce_positive_int, from_field="NO_FREQS"
        ),
        OneToOneFieldMap(
            to_field="num_sites", converter=coerce_positive_int, from_field="NO_SITES"
        ),
    ]
    form_class = PreliminaryCaseForm
    form_defaults = {"data_source": ACCESS_PRELIM_APPLICATION}


PCASE_FORM_MAP = PcaseFormMap()

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
                "data_source": ACCESS_PRELIM_APPLICATION,
                "comments": "Imported by script",
            },
        },
    )()
    for n in range(1, 4)
]
