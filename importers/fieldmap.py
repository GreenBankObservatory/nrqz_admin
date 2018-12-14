"""Provides utilities for mapping header->field

The problem: we have a bunch of Excel files, e.g., that have columnar data we
wish to create model instances from. Each column should map to a field, but
the columns don't always have the same names between Excel files. So, we need
some way to map all possible column headers to their appropriate field.

Additionally, we need a way to link a "converter" to each pairing -- this is
responsible for cleaning the data and converting it to the proper type. For
example, if we have a boolean column that represents None as either "" or "n/a",
depending on the file, we need a way to say that all of those mean the same thing.

This module contains all of the converters and the FieldMap class itself,
as well as an dictionary of every known header to its mapped field -- "expanded"
from the list of FieldMap instances
"""

from itertools import chain
import re
import string

from utils.coord_utils import dms_to_dd


COORD_PATTERN_STR = (
    r"^(?P<degrees>\d+)\s+(?P<minutes>\d+)\s+(?P<seconds>\d+(?:\.\d+)?)$"
)
COORD_PATTERN = re.compile(COORD_PATTERN_STR)


def coerce_bool(value):
    """Coerce a string to a bool, or to None"""

    clean_value = str(value).strip().lower()
    if clean_value in ["yes"]:
        return True
    elif clean_value in ["no", "n0"]:
        return False
    elif clean_value in ["", "na", "n/a"]:
        return None
    else:
        raise ValueError("Could not determine truthiness of value {!r}".format(value))


def coerce_str(value):
    clean_value = str(value).strip().lower()
    if clean_value in ["", "na", "n/a", "#n/a"]:
        return None
    else:
        return value


def coerce_num(value):
    """Coerce a string to a number, or to None"""

    clean_value = str(value).strip().lower()
    if clean_value in ["", "na", "n/a", "no", "#n/a"]:
        return None

    if clean_value == "quad":
        clean_value = 4
    elif clean_value == "hex":
        clean_value = 6
    elif clean_value == "deca":
        clean_value = 10
    else:
        clean_value = re.sub(f"[{string.ascii_letters}]", "", clean_value)

    return float(clean_value)


def coerce_coords(value):
    """Given a coordinate in DD MM SS.sss format, return it in DD.ddd format"""
    clean_value = str(value).strip().lower()

    if clean_value in ["", "none", "#n/a"]:
        return None
    try:
        dd = float(value)
    except ValueError:
        match = re.match(COORD_PATTERN, clean_value)
        if not match:
            raise ValueError(f"Regex {COORD_PATTERN_STR} did not match value {value}")

        dd = dms_to_dd(**match.groupdict())
    return dd


def coerce_lat(value):
    return coerce_coords(value)


def coerce_long(value):
    # Need to invert this because all of our longitudes will be W
    longitude = coerce_coords(value)
    if longitude is not None:
        return -1 * longitude
    else:
        return None


class FieldMapError(ValueError):
    pass


class FormMap:
    """Simple mapping of ModelForm -> field-mapped data"""

    def __init__(
        self, field_maps, form_class=None, form_defaults=None, form_kwargs=None
    ):
        # super().__init__(field_maps)
        self.field_maps = field_maps
        self.form_class = form_class
        if form_defaults:
            self.form_defaults = form_defaults
        else:
            form_defaults = {}
        if form_kwargs:
            self.form_kwargs = form_kwargs
        else:
            self.form_kwargs = {}
        # self.form = form_class() if self.form_class else None

    # def foo(self, data):
    #     self.from_fields = data.keys()

    def render(self, data, extra=None):
        if extra is None:
            extra = {}

        rendered = {}
        for field_map in self.field_maps:
            # aliases = field_map.from_field_aliases
            if field_map.from_fields is None:
                import ipdb

                ipdb.set_trace()
            from_fields = field_map.from_fields
            to_fields = field_map.to_fields
            # converter = field_map.converter

            # TODO: Seems weird that this isn't used...
            for to_field in to_fields:
                try:
                    from_field_data = {
                        from_field: data[from_field] for from_field in from_fields
                    }
                except KeyError as error:
                    continue
                    raise KeyError("All to_fields must be mapped!")

                rendered.update(field_map.map(**from_field_data))

        if self.form_class:
            return self.form_class(
                {**self.form_defaults, **extra, **rendered}, **self.form_kwargs
            )
        return rendered

    def __repr__(self):
        field_maps_str = "\n  ".join([str(field_map) for field_map in self.field_maps])
        return f"FormMap {{\n  {field_maps_str}\n}}"


class FieldMap:
    """Map field to its associated headers and to a converter"""

    ONE_TO_ONE = "1:1"
    ONE_TO_MANY = "1:*"
    MANY_TO_ONE = "*:1"
    MANY_TO_MANY = "*:*"

    def __init__(
        self,
        to_field=None,
        to_fields=None,
        converter=None,
        from_fields=None,
        from_field=None,
    ):
        if isinstance(to_fields, str) or isinstance(from_fields, str):
            raise ValueError("to_fields and from_fields should not be strings!")

        if to_fields and to_field:
            raise ValueError("Cannot provide both to_fields and to_field")

        # Headers the to_field could potentially be associated with
        if to_field:
            self.to_fields = [to_field]
        else:
            self.to_fields = to_fields
        if not self.to_fields:
            raise ValueError("Either to_field or to_fields must be provided!")

        if from_field:
            self.from_fields = [from_field]
        else:
            self.from_fields = from_fields

        if not self.from_fields:
            raise ValueError("Either from_field or from_fields must be provided!")

        if isinstance(from_fields, dict):
            self.aliases = {
                alias: to_field
                for to_field, aliases in from_fields.items()
                for alias in aliases
            }
        else:
            self.aliases = {}

        if not converter and (len(self.to_fields) > 1 or len(self.from_fields) > 1):
            raise ValueError(
                "A custom converter must be given if either to_fields or "
                "from_fields has more than one value!"
            )
        # Function to convert/clean data
        self.converter = converter if converter else self.nop_converter

        from_many = not len(self.from_fields) == 1
        to_many = not len(self.to_fields) == 1
        if from_many and to_many:
            self.map_type = self.MANY_TO_MANY
        elif from_many:
            self.map_type = self.MANY_TO_ONE
        elif to_many:
            self.map_type = self.ONE_TO_MANY
        else:
            self.map_type = self.ONE_TO_ONE

    def nop_converter(self, value):
        """Perform no conversion; simply return value"""
        return value

    def __repr__(self):
        if len(self.from_fields) == 1:
            from_ = "1"
            from_fields = self.from_fields[0]
        else:
            from_ = "*"
            from_fields = self.from_fields

        if len(self.to_fields) == 1:
            to = "1"
            to_fields = self.to_fields[0]
        else:
            to = "*"
            to_fields = self.to_fields

        return f"FieldMap: {from_fields!r} [{from_}]—({self.converter.__name__})—[{to}] {to_fields!r}"
        # return f"FieldMap: {self.converter.__name__}({from_fields!r}) -> {to_fields!r}"

    def map(self, **kwargs):
        if self.aliases:
            unmapped_from_fields = [key not in self.aliases for key in kwargs]
            if any(unmapped_from_fields):
                raise ValueError(
                    f"Found fields {unmapped_from_fields} with no known alias."
                    f"Known aliases: {self.aliases}"
                )

        ret = {self.aliases.get(key, key): value for key, value in kwargs.items()}

        # Handle the simple 1:1 case here to save on boilerplate externally
        # That is, by handling this case here we avoid similar logic
        # propagating to all of our simple converter functions
        if self.map_type == self.ONE_TO_ONE:
            to_field = self.to_fields[0]
            from_field_value = next(iter(ret.values()))
            return {to_field: self.converter(from_field_value)}

        # For all other cases, expect the converter to be smart enough
        return self.converter(**ret)
