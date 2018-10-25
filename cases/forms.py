from django import forms
from cases.models import Case, Facility, LetterTemplate

from crispy_forms.layout import Submit, Layout, Button, Fieldset, Div, Reset
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import FormActions
from dal import autocomplete


class LetterFormHelper(FormHelper):
    form_method = "get"
    layout = Layout(
        Div(
            Div("case", css_class="col"),
            Div("nrqz_id", css_class="col"),
            css_class="row",
        ),
        # FormActions(Submit("submit", "Submit")),
    )


class LetterTemplateForm(forms.Form):
    # cases = forms.ModelMultipleChoiceField(widget=forms.HiddenInput(), required=False)
    cases = forms.ModelMultipleChoiceField(
        queryset=Case.objects.all(),
        # to_field_name="case_num",
        widget=autocomplete.ModelSelect2Multiple(
            url="case_autocomplete", attrs={"data-placeholder": "Case Num"}
        ),
        required=False,
    )
    facilities = forms.ModelMultipleChoiceField(
        queryset=Facility.objects.all(),
        # to_field_name="case_num",
        widget=autocomplete.ModelSelect2Multiple(
            url="facility_autocomplete", attrs={"data-placeholder": "NRQZ ID"}
        ),
        required=False,
    )
    # facilities = forms.ModelMultipleChoiceField(
    #     queryset=Facility.objects.all(),
    #     to_field_name="nrqz_id",
    # )
    template = forms.ModelChoiceField(
        queryset=LetterTemplate.objects.all(),
        empty_label=None,
        to_field_name="name",
        # widget=forms.Select(attrs={"onchange": "this.form.submit()"}),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(LetterTemplateForm, self).__init__(*args, **kwargs)
        self.helper = LetterFormHelper()
