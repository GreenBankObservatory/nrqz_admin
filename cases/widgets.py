"""Custom field widgets for cases app"""

from django import forms
from django_filters import widgets


class PointWidget(widgets.SuffixedMultiWidget):
    template_name = "cases/point_field.html"
    suffixes = ["lat", "long", "radius", "unit"]

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
            forms.TextInput(attrs={"placeholder": "latitude", **attrs}),
            forms.TextInput(attrs={"placeholder": "longitude", **attrs}),
            forms.NumberInput(attrs={"placeholder": "radius", **attrs}),
            forms.Select(attrs=attrs, choices=unit_choices),
        )
        super().__init__(_widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.coords[0], value.coords[1]]
        return [None, None]
