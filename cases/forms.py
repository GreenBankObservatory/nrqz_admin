"""Forms for cases app"""

from django import forms

from dal import autocomplete

from cases.models import Batch, Case, Facility, LetterTemplate, Structure
from .form_helpers import LetterFormHelper


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


class StructureForm(forms.ModelForm):
    class Meta:
        model = Structure
        fields = (
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


class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = (
            "applicant",
            "contact",
            "comments",
            "case_num",
            "name",
            "batch",
            "attachments",
            "completed",
            "shutdown",
            "completed_on",
            "sgrs_notify",
            "sgrs_notified_on",
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
        )


class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ("comments", "attachments", "name")


class FacilityForm(forms.ModelForm):
    class Meta:
        model = Facility
        fields = (
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
            "msl",
            "max_aerpd",
            "max_erp_per_tx",
            "max_gain",
            "max_tx_power",
            "nrao_aerpd",
            "power_density_limit",
            "sgrs_approval",
            "tap_file",
            "tap",
            "tx_power",
            "aeirp_to_gbt",
            "az_bearing",
            "num_tx_per_facility",
        )
