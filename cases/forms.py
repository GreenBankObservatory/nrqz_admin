"""Forms for cases app"""

from django import forms
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.postgres.forms import SimpleArrayField

from dal import autocomplete

from .models import (
    Attachment,
    Boundaries,
    Case,
    Facility,
    LetterTemplate,
    Location,
    Person,
    PreliminaryCase,
    PreliminaryFacility,
    Structure,
)
from .form_helpers import LetterFormHelper
from .fields import PointField
from .widgets import PCaseWidget, CaseWidget, PersonWidget, AttachmentsWidget


class LetterTemplateForm(forms.Form):
    cases = forms.ModelMultipleChoiceField(
        queryset=Case.objects.all(),
        to_field_name="case_num",
        widget=autocomplete.ModelSelect2Multiple(
            url="case_autocomplete", attrs={"data-placeholder": "Case Num"}
        ),
        required=False,
        help_text="Select a set of cases to generate a letter for",
    )
    facilities = forms.ModelMultipleChoiceField(
        queryset=Facility.objects.all(),
        # TODO: This isn't unique; can't use it!
        # to_field_name="nrqz_id",
        widget=autocomplete.ModelSelect2Multiple(
            url="facility_autocomplete", attrs={"data-placeholder": "NRQZ ID"}
        ),
        required=False,
        help_text=(
            "Select Facilities that are not included in any of the "
            "Cases you have selected. This should only rarely be used!"
        ),
    )
    template = forms.ModelChoiceField(
        queryset=LetterTemplate.objects.all(),
        empty_label=None,
        to_field_name="name",
        required=False,
        help_text=(
            "Select a template to render below. This will determine "
            'the "type" of letter (concur, non-concur, etc.)'
        ),
    )

    def __init__(self, *args, **kwargs):
        super(LetterTemplateForm, self).__init__(*args, **kwargs)
        self.helper = LetterFormHelper()

    def clean(self):
        cleaned_data = super().clean()
        cases = cleaned_data["cases"]
        facilities = cleaned_data["facilities"]
        if not (cases or facilities):
            raise forms.ValidationError(
                "At least one of Cases or Facilities must be populated!"
            )

        if facilities:
            cases |= Case.objects.filter(facilities__in=facilities.values("id"))

        if cases.count() != 1:
            raise forms.ValidationError(
                f"There should only be one unique case! Got {cases.count()}!"
            )

        cleaned_data["cases"] = cases

        return cleaned_data


class StructureForm(forms.ModelForm):
    class Meta:
        model = Structure
        fields = (
            "asr",
            "faa_circ_num",
            "faa_study_num",
            "file_num",
            "height",
            "issue_date",
            "location",
        )


class StructureImportForm(StructureForm):
    Meta = StructureForm.Meta
    Meta.fields = sorted([*Meta.fields, "data_source"])


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = (
            "city",
            "comments",
            "county",
            "email",
            "fax",
            "name",
            "phone",
            "state",
            "street",
            "zipcode",
        )


class PersonImportForm(PersonForm):
    Meta = PersonForm.Meta
    Meta.fields = sorted([*Meta.fields, "data_source"])


_BASE_CASE_FIELDS = (
    "applicant",
    "attachments",
    "case_num",
    "comments",
    "completed",
    "completed_on",
    "contact",
    "date_recorded",
    "is_federal",
    "num_freqs",
    "num_sites",
    "original_created_on",
    "original_modified_on",
    "radio_service",
)


class PreliminaryCaseForm(forms.ModelForm):
    class Meta:
        model = PreliminaryCase
        fields = sorted((*_BASE_CASE_FIELDS, "case", "pcase_group"))


class PreliminaryCaseImportForm(PreliminaryCaseForm):
    Meta = PreliminaryCaseForm.Meta
    Meta.fields = sorted([*Meta.fields, "data_source"])


class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = sorted(
            (
                *_BASE_CASE_FIELDS,
                "agency_num",
                "call_sign",
                "original_meets_erpd_limit",
                "fcc_file_num",
                "freq_coord",
                "num_outside",
                "sgrs_notify",
                "sgrs_responded_on",
                "sgrs_service_num",
                "shutdown",
                "si",
                "si_done",
                "si_waived",
            )
        )

        widgets = {
            "applicant": PersonWidget(),
            "contact": PersonWidget(),
            "attachments": AttachmentsWidget(),
        }


class CaseImportForm(CaseForm):
    Meta = CaseForm.Meta
    Meta.fields = sorted([*Meta.fields, "data_source"])


class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = sorted(("path", "comments", "original_index"))


class AttachmentImportForm(AttachmentForm):
    Meta = AttachmentForm.Meta
    Meta.fields = sorted([*Meta.fields, "data_source"])


BASE_FACILITY_FIELDS = (
    "agl",
    "amsl",
    "antenna_model_number",
    "attachments",
    "az_bearing",
    "comments",
    "freq_high",
    "freq_low",
    "latitude",
    "location",
    "location_description",
    "longitude",
    "nrao_aerpd_analog",
    "nrao_aerpd_cdma",
    "nrao_aerpd_cdma2000",
    "nrao_aerpd_gsm",
    "nrao_diff",
    "nrao_space",
    "nrao_tropo",
    "nrqz_id",
    "original_created_on",
    "original_modified_on",
    "original_outside_nrqz",
    "original_srs",
    "power_density_limit",
    "propagation_model",
    "radio_service",
    "requested_max_erp_per_tx",
    "site_name",
    "site_num",
    "survey_1a",
    "survey_2c",
    "topo_12_point",
    "topo_4_point",
    "tpa",
    "usgs_dataset",
)


class BasePreliminaryFacilityForm(forms.ModelForm):
    class Meta:
        model = PreliminaryFacility
        fields = sorted((*BASE_FACILITY_FIELDS, "pcase"))
        widgets = {"pcase": PCaseWidget(), "attachments": AttachmentsWidget()}


class PreliminaryFacilityImportForm(BasePreliminaryFacilityForm):
    Meta = BasePreliminaryFacilityForm.Meta
    Meta.fields = sorted([*Meta.fields, "data_source"])


class PreliminaryFacilityForm(BasePreliminaryFacilityForm):
    # We DO NOT want this when importing; it interferes with our conversions
    location = PointField()


class BaseFacilityForm(forms.ModelForm):
    class Meta:
        model = Facility
        fields = sorted(
            (
                *BASE_FACILITY_FIELDS,
                "aeirp_to_gbt",
                "antenna_gain",
                "band_allowance",
                "bandwidth",
                "call_sign",
                "case",
                "distance_to_first_obstacle",
                "dominant_path",
                "electrical_downtilt",
                "emissions",
                "fcc_file_number",
                "height_of_first_obstacle",
                "main_beam_orientation",
                "max_aerpd",
                "max_eirp",
                "max_gain",
                "max_tx_power",
                "mechanical_downtilt",
                "nrao_aerpd",
                "meets_erpd_limit",
                "num_tx_per_facility",
                "s367",
                "sgrs_approval",
                "sgrs_responded_on",
                "structure",
                "system_loss",
                "tap_file",
                "tx_per_sector",
                "tx_power",
            )
        )

        widgets = {"case": CaseWidget(), "attachments": AttachmentsWidget()}


class FacilityImportForm(BaseFacilityForm):
    Meta = BaseFacilityForm.Meta
    Meta.fields = sorted([*Meta.fields, "data_source"])


class FacilityForm(BaseFacilityForm):
    # We DO NOT want this when importing; it interferes with our conversions
    location = PointField()


class BoundariesForm(forms.ModelForm):
    class Meta:
        model = Boundaries
        fields = ("name", "bounds")


class LocationForm(forms.ModelForm):
    location = PointField()

    class Meta:
        model = Location
        fields = ("name", "location")
