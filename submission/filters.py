import django_filters
from crispy_forms.layout import Submit, Layout, ButtonHolder, Div
from crispy_forms.helper import FormHelper

from . import models

def discover_fields(layout):
    """Discover all fields defined in a layout object

    This is used to avoid defining the field list in two places --
    the layout object is instead inspected to determine the list
    """

    fields = []
    try:
        comps = list(layout)
    except TypeError:
        return fields
    for comp in comps:
        if isinstance(comp, str):
            fields.append(comp)
        else:
            fields.extend(discover_fields(comp))

    return fields


class HelpedFilterSet(django_filters.FilterSet):
    """A FilterSet with a Crispy Form Helper class"""

    def __init__(self, *args, **kwargs):
        super(HelpedFilterSet, self).__init__(*args, **kwargs)
        self.form.helper = self.Meta.formhelper_class()


class FacilityFilterFormHelper(FormHelper):
    """Provides layout information for FacilityFilter.form"""
    form_method = "get"
    layout = Layout(
        Div(
            Div("site_name", "nrqz_id", css_class="col"),
            Div("latitude", "longitude", css_class="col"),
            Div("amsl", "agl", css_class="col"),
            Div("freq_low", "freq_high", css_class="col"),
            css_class="row",
        ),
        ButtonHolder(Submit("submit", "Filter")),
    )


class FacilityFilter(HelpedFilterSet):
    site_name = django_filters.CharFilter(lookup_expr='icontains')
    nrqz_id = django_filters.CharFilter(lookup_expr='icontains')
    call_sign = django_filters.CharFilter(lookup_expr='icontains')
    latitude = django_filters.CharFilter(lookup_expr='startswith')
    longitude = django_filters.CharFilter(lookup_expr='startswith')
    freq_low = django_filters.RangeFilter(lookup_expr='range')
    freq_high = django_filters.RangeFilter(lookup_expr='range')
    amsl = django_filters.RangeFilter(lookup_expr='range')
    agl = django_filters.RangeFilter(lookup_expr='range')

    class Meta:
        model = models.Facility
        formhelper_class = FacilityFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class SubmissionFilterFormHelper(FormHelper):
    """Provides layout information for SubmissionFilter.form"""

    form_method = "get"
    layout = Layout(
        Div(
            Div("created_on", css_class="col"),
            Div("name", css_class="col"),
            Div("comments", css_class="col"),
            css_class="row",
        ),
        ButtonHolder(Submit("submit", "Filter")),
    )


class SubmissionFilter(HelpedFilterSet):
    created_on = django_filters.DateFromToRangeFilter(lookup_expr="range")
    name = django_filters.CharFilter(lookup_expr='icontains')
    comments = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = models.Submission
        formhelper_class = SubmissionFilterFormHelper
        fields = discover_fields(formhelper_class.layout)
