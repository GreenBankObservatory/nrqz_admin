from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.error import GEOSException
from django import forms
import django_filters
from crispy_forms.layout import Submit, Layout, Button, Div, Reset
from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper

from utils.coord_utils import dms_to_dd, parse_coord
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


class CollapsibleFilterFormLayout(Layout):
    def __init__(self, *args):
        super(CollapsibleFilterFormLayout, self).__init__(
            Div(
                *args,
                FormActions(
                    Submit("submit", "Filter"),
                    Reset("reset", "Reset"),
                    Submit(
                        "kml",
                        "As .kml",
                        title=(
                            "Download the locations of all currently-filtered "
                            "Facilities as a .kml file"
                        ),
                    ),
                ),
                css_class="container",
            )
        )


class BatchFilterFormHelper(FormHelper):
    """Provides layout information for FacilityFilter.form"""

    form_method = "get"
    form_class = "collapse"
    form_id = "batch-filter-form"
    layout = CollapsibleFilterFormLayout(
        Div(
            Div("name", css_class="col"),
            Div("comments", css_class="col"),
            css_class="row",
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
    form_class = "collapse show"
    form_id = "facility-filter-form"
    layout = CollapsibleFilterFormLayout(
        Div(
            Div("nrqz_id", "site_name", css_class="col"),
            Div("location", "freq_low", "freq_high", css_class="col"),
            css_class="row",
        ),
    )


class PointWidget(django_filters.widgets.SuffixedMultiWidget):
    template_name = "cases/point_field.html"
    suffixes = ["lat", "long"]

    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        _widgets = (
            forms.TextInput(attrs={"placeholder": "latitude", **attrs}),
            forms.TextInput(attrs={"placeholder": "longitude", **attrs}),
        )
        super().__init__(_widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.coords[0], value.coords[1]]
        return [None, None]


class PointField(forms.MultiValueField):
    widget = PointWidget

    def __init__(self, fields=None, *args, **kwargs):
        error_messages = {"incomplete": "Enter both a latitude and a longitude"}
        if fields is None:
            fields = (
                forms.CharField(
                    error_messages={"invalid": "Enter a valid latitude"},
                    validators=[self.coord_validator],
                ),
                forms.CharField(
                    error_messages={"invalid": "Enter a valid longitude"},
                    validators=[self.coord_validator],
                ),
            )
        super().__init__(fields, *args, **kwargs, error_messages=error_messages)

    def coord_validator(self, coord):
        try:
            return parse_coord(coord)
        except ValueError:
            raise forms.ValidationError(self.error_messages["invalid"], code="invalid")

    def compress(self, data_list):
        if data_list:
            if len(data_list) != 2:
                raise forms.ValidationError(f"Expected 2 values; got {len(data_list)}")

            latitude_orig = data_list[0]
            longitude_orig = data_list[1]

            try:
                latitude = parse_coord(latitude_orig)
                print(f"latitude converted from {latitude_orig!r} {latitude!r}")
                longitude = parse_coord(longitude_orig)
                print(f"longitude converted from {longitude_orig!r} {longitude!r}")
            except ValueError as error:
                print("ValidationError")
                raise forms.ValidationError(
                    "Valid latitude and longitude must be given!"
                ) from error

            try:
                value = GEOSGeometry(f"Point({longitude} {latitude})")
            except (ValueError, GEOSException):
                raise forms.ValidationError(
                    f"Failed to create Point from ({latitude_orig}, {longitude_orig})!"
                )
            return value

        return None


class PointFilter(django_filters.Filter):
    field_class = PointField

    def filter(self, qs, value):
        if value:
            print("value: ", value)
            return qs.filter(location__distance_lte=(value, 1000))
        else:
            return super().filter(qs, value)


# class DistanceFilterField(django_filters.Field):
#     def method(self, queryset, lookup, value):
#         pnt = GEOSGeometry(value, srid=4326)
#         return models.Facility.objects.filter(location__distance_lte=(pnt, 1000))

# class DistanceFilter(django_filters.FilterSet):
#     class Meta:
#         model = Facility


class FacilityFilter(HelpedFilterSet):
    site_name = django_filters.CharFilter(lookup_expr="icontains")
    nrqz_id = django_filters.CharFilter(lookup_expr="icontains")
    call_sign = django_filters.CharFilter(lookup_expr="icontains")
    freq_low = django_filters.NumericRangeFilter()
    freq_high = django_filters.NumericRangeFilter()
    amsl = django_filters.NumericRangeFilter()
    agl = django_filters.NumericRangeFilter()
    location = PointFilter()

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
