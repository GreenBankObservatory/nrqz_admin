from django import forms
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.error import GEOSException

import django_filters

from utils.coord_utils import parse_coord
from .widgets import PointWidget


class PointField(forms.MultiValueField):
    widget = PointWidget

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
                    error_messages={"invalid": "Enter a valid latitude"},
                    validators=[self.coord_validator],
                ),
                forms.CharField(
                    error_messages={"invalid": "Enter a valid longitude"},
                    validators=[self.coord_validator],
                ),
                forms.FloatField(min_value=0),
                django_filters.fields.ChoiceField(choices=unit_choices),
            )

        super().__init__(fields, *args, **kwargs, error_messages=error_messages)

    def coord_validator(self, coord):
        try:
            return parse_coord(coord)
        except ValueError:
            raise forms.ValidationError(self.error_messages["invalid"], code="invalid")

    def compress(self, data_list):
        print("data list", data_list)
        if data_list:
            expected_length = 4
            if len(data_list) != expected_length:
                raise forms.ValidationError(
                    f"Expected {expected_length} values; got {len(data_list)}"
                )

            latitude_orig = data_list[0]
            longitude_orig = data_list[1]
            radius = data_list[2]
            unit = data_list[3]

            latitude_clean = latitude_orig.strip()
            longitude_clean = longitude_orig.strip()

            # If we have neither latitude nor longitude, don't attempt
            # to create a Point, just bail
            if not (latitude_clean or longitude_clean or radius):
                return None

            if (latitude_clean or longitude_clean) and not radius:
                raise forms.ValidationError("All location fields must be provided!")

            print("Now parsing latlong")
            try:
                latitude = parse_coord(latitude_orig)
                print(f"latitude converted from {latitude_orig!r} {latitude!r}")
                longitude = parse_coord(longitude_orig)
                print(f"longitude converted from {longitude_orig!r} {longitude!r}")
            except ValueError as error:
                print("ValidationError")
                raise forms.ValidationError(
                    "All location fields must be provided!"
                ) from error

            try:
                point = GEOSGeometry(f"Point({longitude} {latitude})")
            except (ValueError, GEOSException):
                raise forms.ValidationError(
                    f"Failed to create Point from ({latitude_orig}, {longitude_orig})!"
                )
            return (point, radius, unit)

        return None
