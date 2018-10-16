import django_filters
from crispy_forms.layout import Submit, Layout, ButtonHolder, Div
from crispy_forms.helper import FormHelper

from applicants.models import Applicant
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


class BatchFilterFormHelper(FormHelper):
    """Provides layout information for FacilityFilter.form"""

    form_method = "get"
    layout = Layout(
        Div(
            Div("name", "comments", css_class="col"),
            css_class="row",
        ),
        ButtonHolder(
            Submit("submit", "Filter"),
        ),
    )

class BatchFilter(HelpedFilterSet):
    class Meta:
        model = models.Batch
        formhelper_class = BatchFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class FacilityFilterFormHelper(FormHelper):
    """Provides layout information for FacilityFilter.form"""

    form_method = "get"
    layout = Layout(
        Div(
            Div("nrqz_id", "site_name", css_class="col"),
            Div("latitude", "longitude", css_class="col"),
            # Div("amsl", "agl", css_class="col"),
            Div("freq_low", "freq_high", css_class="col"),
            # Div("submission", css_class="col"),
            css_class="row",
        ),
        ButtonHolder(
            Submit("submit", "Filter"),
            Submit(
                "kml",
                "As .kml",
                title=(
                    "Download the locations of all currently-filtered "
                    "Facilities as a .kml file"
                ),
            ),
        ),
    )


class FacilityFilter(HelpedFilterSet):
    site_name = django_filters.CharFilter(lookup_expr="icontains")
    nrqz_id = django_filters.CharFilter(lookup_expr="icontains")
    call_sign = django_filters.CharFilter(lookup_expr="icontains")
    latitude = django_filters.CharFilter(lookup_expr="startswith")
    longitude = django_filters.CharFilter(lookup_expr="startswith")
    freq_low = django_filters.RangeFilter(lookup_expr="range")
    freq_high = django_filters.RangeFilter(lookup_expr="range")
    amsl = django_filters.RangeFilter(lookup_expr="range")
    agl = django_filters.RangeFilter(lookup_expr="range")

    class Meta:
        model = models.Facility
        formhelper_class = FacilityFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class SubmissionFilterFormHelper(FormHelper):
    """Provides layout information for SubmissionFilter.form"""

    form_method = "get"
    layout = Layout(
        Div(
            Div("case_num", css_class="col"),
            Div("applicant", css_class="col"),
            Div("batch", css_class="col"),
            css_class="row",
        ),
        ButtonHolder(
            Submit("submit", "Filter"),
            Submit(
                "kml",
                "As .kml",
                title=(
                    "Download the locations of all facilities linked to "
                    "the currently-filtered Submissions as a .kml file"
                ),
            ),
        ),
    )


class SubmissionFilter(HelpedFilterSet):
    created_on = django_filters.DateFromToRangeFilter(lookup_expr="range")
    name = django_filters.CharFilter(lookup_expr="icontains")
    comments = django_filters.CharFilter(lookup_expr="icontains")
    applicant = django_filters.CharFilter(label="Applicant name contains", lookup_expr="applicant__icontains")
    batch = django_filters.CharFilter(lookup_expr="name__icontains")

    class Meta:
        model = models.Submission
        formhelper_class = SubmissionFilterFormHelper
        fields = discover_fields(formhelper_class.layout)
