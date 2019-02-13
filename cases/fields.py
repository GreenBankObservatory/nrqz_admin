"""Custom form fields for cases app"""

from django import forms
from django.contrib.gis.geos import Point
from django.contrib.gis.geos.error import GEOSException

import django_filters

from utils.coord_utils import parse_coords
from .widgets import PointWidget, PointSearchWidget


class PointField(forms.CharField):
    widget = PointWidget

    def to_python(self, value):
        if not value:
            return None

        if isinstance(value, Point):
            return value.transform(4326)

        try:
            latitude, longitude = parse_coords(value)
        except ValueError as error:
            raise forms.ValidationError(error)
        return Point(x=longitude, y=latitude, srid=4326)


class PointSearchField(forms.MultiValueField):
    widget = PointSearchWidget

    def __init__(self, *args, fields=None, unit_choices=None, **kwargs):
        if unit_choices is None:
            unit_choices = [
                ("m", "Meters"),
                ("km", "Kilometers"),
                ("ft", "Feet"),
                ("mi", "Miles"),
            ]

        error_messages = {"incomplete": "Enter both a latitude and a longitude"}
        if fields is None:
            fields = (
                forms.CharField(
                    error_messages={
                        "invalid": "Enter a valid, comma-separated coordinate pair"
                    },
                    validators=[self.coord_validator],
                ),
                forms.FloatField(min_value=0),
                django_filters.fields.ChoiceField(choices=unit_choices),
            )

        super().__init__(fields, *args, **kwargs, error_messages=error_messages)

    def coord_validator(self, coords):
        try:
            return parse_coords(coords)
        except ValueError:
            raise forms.ValidationError(self.error_messages["invalid"], code="invalid")

    def compress(self, data_list):
        # print("data list", data_list)
        if data_list:
            expected_length = 3
            if len(data_list) != expected_length:
                raise forms.ValidationError(
                    f"Expected {expected_length} values; got {len(data_list)}"
                )

            coords_orig = data_list[0]
            radius = data_list[1]
            unit = data_list[2]

            coords_clean = coords_orig.strip()

            # If we have neither latitude nor longitude, don't attempt
            # to create a Point, just bail
            if not (coords_clean or radius):
                return None

            if coords_clean and not radius:
                raise forms.ValidationError("All location fields must be provided!")

            # print("Now parsing latlong")
            try:
                latitude, longitude = parse_coords(coords_clean)
                # print(f"latitude converted from {latitude_orig!r} {latitude!r}")
                # print(f"longitude converted from {longitude_orig!r} {longitude!r}")
            except ValueError as error:
                # print("ValidationError")
                raise forms.ValidationError(
                    "All location fields must be provided!"
                ) from error

            try:
                point = Point(f"Point({longitude} {latitude})")
            except (ValueError, GEOSException):
                raise forms.ValidationError(
                    f"Failed to create Point from ({coords_orig})!"
                )
            return (point, radius, unit)

        return None
