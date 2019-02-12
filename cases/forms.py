"""Forms for cases app"""

from django import forms
from django.contrib.gis.geos import GEOSGeometry

from dal import autocomplete

from .models import (
    Attachment,
    Case,
    Person,
    PreliminaryFacility,
    PreliminaryCase,
    Facility,
    LetterTemplate,
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
        print("clenanana")
        cleaned_data = super().clean()
        if not (cleaned_data.get("cases") or self.cleaned_data.get("facilities")):
            raise forms.ValidationError(
                "At least one of Cases or Facilities must be populated!"
            )

        return cleaned_data


class StructureForm(forms.ModelForm):
    class Meta:
        model = Structure
        fields = (
            "data_source",
            "asr",
            "file_num",
            "location",
            "faa_circ_num",
            "faa_study_num",
            "issue_date",
            "height",
            # "owner",
            # "contact",
            # "facility",
        )


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = (
            "data_source",
            "name",
            "phone",
            "fax",
            "email",
            "street",
            "city",
            "county",
            "state",
            "zipcode",
            "comments",
        )


class PreliminaryCaseForm(forms.ModelForm):
    class Meta:
        model = PreliminaryCase
        fields = (
            "original_created_on",
            "original_modified_on",
            "data_source",
            "applicant",
            "contact",
            "pcase_group",
            "comments",
            "case_num",
            "name",
            "case",
            "attachments",
            "completed",
            "completed_on",
            "radio_service",
            "num_freqs",
            "num_sites",
        )


class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = (
            "original_created_on",
            "original_modified_on",
            "data_source",
            "applicant",
            "contact",
            "comments",
            "case_num",
            "name",
            "attachments",
            "completed",
            "shutdown",
            "completed_on",
            "sgrs_notify",
            "sgrs_responded_on",
            "radio_service",
            "call_sign",
            "freq_coord",
            "fcc_file_num",
            "num_freqs",
            "num_sites",
            "num_outside",
            "erpd_limit",
            "si_waived",
            "si",
            "si_done",
            "agency_num",
            "date_recorded",
        )

        widgets = {
            "applicant": PersonWidget(),
            "contact": PersonWidget(),
            "attachments": AttachmentsWidget(),
        }

    #     attachments = forms.ModelMultipleChoiceField(
    #     queryset=Attachment.objects.all(),

    #     help_text="Select a set of cases to generate a letter for",
    # )


class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ("path", "comments")


class PreliminaryFacilityForm(forms.ModelForm):
    class Meta:
        model = PreliminaryFacility
        fields = (
            "original_created_on",
            "original_modified_on",
            "data_source",
            "site_num",
            "original_created_on",
            "freq_low",
            "antenna_model_number",
            "power_density_limit",
            "site_name",
            "latitude",
            "longitude",
            "amsl",
            "agl",
            "comments",
            "location",
            "pcase",
            "attachments",
        )
        widgets = {"pcase": PCaseWidget(), "attachments": AttachmentsWidget()}


class FacilityForm(forms.ModelForm):
    location = PointField()

    class Meta:
        model = Facility
        fields = (
            "original_created_on",
            "original_modified_on",
            "data_source",
            "site_num",
            "freq_low",
            "site_name",
            "call_sign",
            "fcc_file_number",
            "location",
            "latitude",
            "longitude",
            "amsl",
            "agl",
            "freq_high",
            "bandwidth",
            "max_output",
            "antenna_gain",
            "system_loss",
            "main_beam_orientation",
            "mechanical_downtilt",
            "electrical_downtilt",
            "antenna_model_number",
            "nrqz_id",
            "tx_per_sector",
            "tx_antennas_per_sector",
            "technology",
            "uses_split_sectorization",
            "uses_cross_polarization",
            "uses_quad_or_octal_polarization",
            "num_quad_or_octal_ports_with_feed_power",
            "tx_power_pos_45",
            "tx_power_neg_45",
            "asr_is_from_applicant",
            "comments",
            "case",
            "structure",
            "band_allowance",
            "distance_to_first_obstacle",
            "dominant_path",
            "erpd_per_num_tx",
            "height_of_first_obstacle",
            "loc",
            "max_aerpd",
            "max_erp_per_tx",
            "max_gain",
            "max_tx_power",
            "nrao_aerpd",
            "power_density_limit",
            "sgrs_approval",
            "tap_file",
            "tpa",
            "tx_power",
            "aeirp_to_gbt",
            "az_bearing",
            "num_tx_per_facility",
            "nrao_approval",
            "attachments",
        )

        widgets = {"case": CaseWidget(), "attachments": AttachmentsWidget()}
