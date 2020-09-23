"""Forms for cases app"""

from django import forms

from crispy_forms.layout import Submit
from dal.forms import FutureModelForm
from dal import autocomplete
from tempus_dominus.widgets import DatePicker

from utils.misc import put_help_text_in_title

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
from .form_helpers import LetterFormHelper, CaseFormHelper, PersonFormHelper
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
    class Meta(StructureForm.Meta):
        fields = sorted([*StructureForm.Meta.fields, "data_source"])


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = PersonFormHelper()
        self.helper.form_method = "post"


class PersonImportForm(PersonForm):
    class Meta(PersonForm.Meta):
        fields = sorted([*PersonForm.Meta.fields, "data_source"])


_BASE_CASE_FIELDS = (
    "applicant",
    "attachments",
    "case_num",
    "comments",
    "completed",
    "completed_on",
    "contact",
    "date_received",
    "is_federal",
    "num_freqs",
    "num_sites",
    "radio_service",
)


class PreliminaryCaseForm(forms.ModelForm):
    class Meta:
        model = PreliminaryCase
        fields = _BASE_CASE_FIELDS
        widgets = {
            "applicant": PersonWidget(),
            "contact": PersonWidget(),
            "attachments": AttachmentsWidget(),
            "case": CaseWidget(),
        }


class PreliminaryCaseImportForm(PreliminaryCaseForm):
    class Meta(PreliminaryCaseForm.Meta):
        fields = sorted(
            [
                *PreliminaryCaseForm.Meta.fields,
                "data_source",
                "original_created_on",
                "original_modified_on",
            ]
        )


class BaseCaseForm(FutureModelForm):
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
                "original_si_done",
                "si_waived",
            )
        )


@put_help_text_in_title
class CaseForm(BaseCaseForm):
    sgrs_notify = forms.BooleanField(initial=True, label="SGRS Notified")
    is_federal = forms.BooleanField(label="Gov.")

    class Meta(BaseCaseForm.Meta):
        fields = [
            field for field in BaseCaseForm.Meta.fields if field not in ["completed"]
        ]

        widgets = {
            "applicant": PersonWidget({"data-placeholder": "Applicant Name"}),
            "contact": PersonWidget({"data-placeholder": "Contact Name"}),
            "attachments": AttachmentsWidget(),
            "date_received": DatePicker(options={"format": "MM/DD/YY"}),
            "completed_on": DatePicker(options={"format": "MM/DD/YY"}),
            "sgrs_responded_on": DatePicker(options={"format": "MM/DD/YY"}),
            "original_si_done": DatePicker(options={"format": "MM/DD/YY"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = CaseFormHelper()
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Submit"))


class CaseAdminForm(BaseCaseForm):
    sgrs_notify = forms.BooleanField(initial=True, label="SGRS Notified")
    is_federal = forms.BooleanField(label="Gov.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = CaseFormHelper()
        self.helper.form_method = "post"


class CaseImportForm(BaseCaseForm):
    class Meta(BaseCaseForm.Meta):
        fields = sorted(
            [
                *BaseCaseForm.Meta.fields,
                "data_source",
                "original_created_on",
                "original_modified_on",
            ]
        )


class CaseQuickJumpForm(forms.Form):
    jump_to_case_id = forms.ModelChoiceField(
        queryset=Case.objects.all(),
        # to_field_name="case_num",
        widget=autocomplete.ModelSelect2(
            url="case_autocomplete",
            attrs={
                "data-placeholder": "Quick-jump to Case #",
                # "data-select-on-close": True,
                "class": "case-quick-jump-field",
                "accesskey": "c",
                "data-ajax--delay": 0,
            },
        ),
        required=False,
        label="",
    )


class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ("is_active", "file_path", "comments")


class AttachmentImportForm(AttachmentForm):
    class Meta(AttachmentForm.Meta):
        fields = sorted([*AttachmentForm.Meta.fields, "data_source", "original_index"])


BASE_FACILITY_FIELDS = (
    "agency_num",
    "agl",
    "amsl",
    "antenna_model_number",
    "attachments",
    "az_bearing",
    "comments",
    "freq_high",
    "freq_low",
    "location",
    "location_description",
    "nrao_aerpd_analog",
    "nrao_aerpd_cdma",
    "nrao_aerpd_cdma2000",
    "nrao_aerpd_gsm",
    "nrao_diff",
    "nrao_space",
    "nrao_tropo",
    "nrqz_id",
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
    class Meta(BasePreliminaryFacilityForm.Meta):
        fields = sorted(
            [
                *BasePreliminaryFacilityForm.Meta.fields,
                "data_source",
                "original_created_on",
                "original_modified_on",
                "original_outside_nrqz",
                "original_srs",
            ]
        )


class PreliminaryFacilityForm(BasePreliminaryFacilityForm):
    # We DO NOT want this when importing; it interferes with our conversions
    location = PointField()


class BaseFacilityForm(forms.ModelForm):
    case = forms.ModelChoiceField(
        queryset=Case.objects.all(),
        to_field_name="case_num",
        widget=autocomplete.ModelSelect2(
            url="case_autocomplete", attrs={"data-placeholder": "Case Num"}
        ),
        required=True,
    )

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
                "si_done",
                "sgrs_approval",
                "sgrs_responded_on",
                "structure",
                "system_loss",
                "tap_file",
                "tx_per_sector",
                "tx_power",
            )
        )

        widgets = {"attachments": AttachmentsWidget()}


class FacilityImportForm(BaseFacilityForm):
    class Meta(BaseFacilityForm.Meta):
        fields = sorted(
            [
                *BaseFacilityForm.Meta.fields,
                "data_source",
                "original_created_on",
                "original_modified_on",
                "original_outside_nrqz",
                "original_srs",
            ]
        )


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


class DuplicateCaseForm(forms.Form):
    num_duplicates = forms.IntegerField(
        min_value=1,
        label="Make Duplicates",
        widget=forms.NumberInput(attrs={"placeholder": "# duplicates"}),
    )
