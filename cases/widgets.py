"""Custom field widgets for cases app"""

from django import forms
from django.contrib.gis.geos import Point

from django_filters import widgets
from dal import autocomplete

from utils.coord_utils import point_to_string, coords_to_string


class PointWidget(forms.widgets.TextInput):
    """
    A Widget that splits Point input into latitude/longitude text inputs.
    """

    def format_value(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            return value

        if isinstance(value, Point):
            return point_to_string(value, concise=True)

        longitude, latitude = value.coords
        return coords_to_string(latitude, longitude, concise=True)


class PointSearchWidget(widgets.SuffixedMultiWidget):
    template_name = "cases/point_field.html"
    suffixes = ["", "radius", "unit"]

    def __init__(self, unit_choices=None, attrs=None):
        if attrs is None:
            attrs = {}

        if unit_choices is None:
            unit_choices = [
                ("m", "Meters"),
                ("km", "Kilometers"),
                ("ft", "Feet"),
                ("mi", "Miles"),
            ]
        _widgets = (
            forms.TextInput(attrs={"placeholder": "coordinates", **attrs}),
            forms.NumberInput(attrs={"placeholder": "radius", **attrs}),
            forms.Select(attrs=attrs, choices=unit_choices),
        )
        super().__init__(_widgets, attrs)

    # def decompress(self, value):
    #     if value:
    #         return [value.coords[0], value.coords[1]]
    #     return [None, None]


PCaseWidget = lambda: autocomplete.ModelSelect2(
    url="pcase_autocomplete", attrs={"data-placeholder": ""}
)
CaseWidget = lambda: autocomplete.ModelSelect2(
    url="case_autocomplete", attrs={"data-placeholder": ""}
)
PersonWidget = lambda: autocomplete.ModelSelect2(
    url="person_autocomplete", attrs={"data-placeholder": ""}
)
AttachmentsWidget = lambda: autocomplete.ModelSelect2Multiple(
    url="attachment_autocomplete", attrs={"data-placeholder": ""}
)

PCasesWidget = lambda: autocomplete.ModelSelect2Multiple(
    url="pcase_autocomplete", attrs={"data-placeholder": ""}
)
CasesWidget = lambda: autocomplete.ModelSelect2Multiple(
    url="case_autocomplete", attrs={"data-placeholder": ""}
)
PFacilitiesWidget = lambda: autocomplete.ModelSelect2Multiple(
    url="pfacility_autocomplete", attrs={"data-placeholder": ""}
)
FacilitiesWidget = lambda: autocomplete.ModelSelect2Multiple(
    url="facility_autocomplete", attrs={"data-placeholder": ""}
)
