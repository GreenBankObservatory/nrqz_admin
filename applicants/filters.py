import django_filters
from crispy_forms.layout import Submit, Layout, ButtonHolder, Div
from crispy_forms.helper import FormHelper

from submission.filters import discover_fields, HelpedFilterSet

from . import models


class ApplicantFilterFormHelper(FormHelper):
    """Provides layout information for ApplicantFilter.form"""

    form_method = "get"
    layout = Layout(
        Div(
            Div("nrqz_no", "applicant", "contact", css_class="col"),
            Div("phone", "email", "state", css_class="col"),
            Div("completed", "shutdown", css_class="col"),
            Div("radio_service", "call_sign", "fcc_num", css_class="col"),
            css_class="row",
        ),
        ButtonHolder(Submit("submit", "Filter")),
    )


class ApplicantFilter(HelpedFilterSet):
    applicant = django_filters.CharFilter(lookup_expr="icontains")
    contact = django_filters.CharFilter(lookup_expr="icontains")
    call_sign = django_filters.CharFilter(lookup_expr="icontains")
    phone = django_filters.CharFilter(lookup_expr="icontains")
    email = django_filters.CharFilter(lookup_expr="icontains")
    fcc_num = django_filters.CharFilter(lookup_expr="icontains")
    state = django_filters.CharFilter(lookup_expr="icontains")
    radio_service = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = models.Applicant
        formhelper_class = ApplicantFilterFormHelper
        fields = discover_fields(formhelper_class.layout)
