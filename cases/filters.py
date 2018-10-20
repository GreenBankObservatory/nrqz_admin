from django.contrib.gis.geos import GEOSGeometry
import django_filters
from crispy_forms.layout import Submit, Layout, Button, Div
from crispy_forms.bootstrap import FormActions
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


class BatchFilterFormHelper(FormHelper):
    """Provides layout information for FacilityFilter.form"""

    form_method = "get"
    form_class = "collapse"
    form_id = "batch-filter-form"
    layout = Layout(
        Div(
            Div(
                Div("name", css_class="col"),
                Div("comments", css_class="col"),
                css_class="row",
            ),
            FormActions(Submit("submit", "Filter")),
            css_class="container"
        )
    )


class BatchFilter(HelpedFilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    comments = django_filters.CharFilter(lookup_expr="icontains")

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
            Div("latitude", "longitude", "location", css_class="col"),
            Div("freq_low", "freq_high", css_class="col"),
            css_class="row",
        ),
        FormActions(
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

# class DistanceFilterField(django_filters.Field):
#     def method 

def foo(queryset, lookup, value):
    pnt = GEOSGeometry(value, srid=4326)
    return models.Facility.objects.filter(location__distance_lte=(pnt, 1000))
    # return queryset.filter(**{lookup: (GEOSGeometry(value, srid=4326), 1000)})

class FacilityFilter(HelpedFilterSet):
    site_name = django_filters.CharFilter(lookup_expr="icontains")
    nrqz_id = django_filters.CharFilter(lookup_expr="icontains")
    call_sign = django_filters.CharFilter(lookup_expr="icontains")
    latitude = django_filters.RangeFilter(lookup_expr="range")
    longitude = django_filters.RangeFilter(lookup_expr="range")
    freq_low = django_filters.RangeFilter(lookup_expr="range")
    freq_high = django_filters.RangeFilter(lookup_expr="range")
    amsl = django_filters.RangeFilter(lookup_expr="range")
    agl = django_filters.RangeFilter(lookup_expr="range")
    location = django_filters.CharFilter(lookup_expr="distance_lte", method=foo)

    class Meta:
        model = models.Facility
        formhelper_class = FacilityFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class CaseFilterFormHelper(FormHelper):
    """Provides layout information for CaseFilter.form"""

    form_method = "get"
    layout = Layout(
        Div(
            Div("case_num", "batch", css_class="col"),
            Div("applicant", "contact", css_class="col"),
            css_class="row",
        ),
        Div(
            Div("completed", "shutdown", css_class="col"),
            Div("radio_service", "call_sign", "fcc_file_num", css_class="col"),
            css_class="row",
        ),
        FormActions(
            Submit("submit", "Filter"),
            Submit(
                "kml",
                "As .kml",
                title=(
                    "Download the locations of all facilities linked to "
                    "the currently-filtered Casess as a .kml file"
                ),
            ),
        ),
    )


class CaseFilter(HelpedFilterSet):
    created_on = django_filters.DateFromToRangeFilter(lookup_expr="range")
    name = django_filters.CharFilter(lookup_expr="icontains")
    comments = django_filters.CharFilter(lookup_expr="icontains")
    batch = django_filters.CharFilter(lookup_expr="name__icontains")
    applicant = django_filters.CharFilter(lookup_expr="name__icontains")
    contact = django_filters.CharFilter(lookup_expr="name__icontains")

    class Meta:
        model = models.Case
        formhelper_class = CaseFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class PersonFilterFormHelper(FormHelper):
    """Provides layout information for PersonFilter.form"""

    form_method = "get"
    layout = Layout(
        Div(
            Div("name", "email", "phone", css_class="col"),
            Div("street", "city", "state", "zipcode", css_class="col"),
            css_class="row",
        ),
        FormActions(Submit("submit", "Filter")),
    )


class PersonFilter(HelpedFilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    email = django_filters.CharFilter(lookup_expr="icontains")
    phone = django_filters.CharFilter(lookup_expr="icontains")
    street = django_filters.CharFilter(lookup_expr="icontains")
    city = django_filters.CharFilter(lookup_expr="icontains")
    state = django_filters.CharFilter(lookup_expr="icontains")
    zipcode = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = models.Person
        formhelper_class = PersonFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class AttachmentFilterFormHelper(FormHelper):
    """Provides layout information for AttachmentFilter.form"""

    form_method = "get"
    layout = Layout(
        Div(
            Div("path", css_class="col"),
            Div("comments", css_class="col"),
            css_class="row",
        ),
        FormActions(Submit("submit", "Filter")),
    )


class AttachmentFilter(HelpedFilterSet):
    path = django_filters.CharFilter(lookup_expr="icontains")
    class Meta:
        model = models.Attachment
        formhelper_class = AttachmentFilterFormHelper
        fields = discover_fields(formhelper_class.layout)
