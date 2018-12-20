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

from django.forms import ModelForm, ValidationError


class FieldMapError(ValueError):
    pass


class FormMap:
    """Simple mapping of ModelForm -> field-mapped data"""

    def __init__(
        self, field_maps, form_class=None, form_defaults=None, form_kwargs=None
    ):
        self.field_maps = field_maps
        self.form_class = form_class

        if form_defaults:
            self.form_defaults = form_defaults
        else:
            self.form_defaults = {}

        if form_kwargs:
            self.form_kwargs = form_kwargs
        else:
            self.form_kwargs = {}

        self.unaliased_map = None
        # self._rendered_form = None

    def unalias(self, data):
        """Unalias!"""

        # TODO: Error checking. Shouldn't have more than one match per alias or something like that
        unaliased = {}
        for field_map in self.field_maps:
            for key in data:
                for from_field_alias, from_field_internal in field_map.aliases.items():
                    if key == from_field_alias:
                        unaliased[from_field_internal] = from_field_alias

        return unaliased

    def render_dict(self, data, allow_unprocessed=True, allow_missing=True):
        rendered = {}
        processed = set()

        if not self.unaliased_map:
            self.unaliased_map = self.unalias(data)

        for field_map in self.field_maps:
            from_field_data = {}

            for from_field in field_map.from_fields:
                # Either get the unaliased value of from_field, or, if one isn't
                # found, just use from_field itself
                data_key = self.unaliased_map.get(from_field, from_field)
                try:
                    from_field_data[data_key] = data[data_key]
                except KeyError as error:
                    if not allow_missing:
                        raise error
                    else:
                        # print(
                        # f"WARNING: Expected key {data_key!r} is missing "
                        # f"from data: {data.keys()}"
                        # )
                        pass

            # print(f"update {from_field_data}")
            rendered.update(field_map.map(**from_field_data))
            processed.update(from_field_data.keys())

        # print("processed")
        # pprint(processed)

        unprocessed = set(data.keys()).difference(processed)
        if unprocessed:
            message = f"Did not process the following data items: {unprocessed}"
            if not allow_unprocessed:
                raise ValueError(message)
            # print(f"WARNING: {message}")

        return rendered

    def render(self, data, extra=None, allow_unprocessed=True, allow_missing=True):
        if not self.form_class:
            raise ValueError("No FormMap.form_class defined; cannot render a form!")
        if extra is None:
            extra = {}
        rendered = self.render_dict(data, allow_unprocessed, allow_missing)
        return self.form_class(
            {**self.form_defaults, **extra, **rendered}, **self.form_kwargs
        )

    def save(self, data, **kwargs):
        # Assume that if data is a ModelForm instance, it is an already-rendered
        # Form.
        if isinstance(data, ModelForm):
            form = data
        # Thus, if it is _not_ a ModelForm instance, we need to render it
        # ourselves
        else:
            form = self.render(data, **kwargs)

        if form.is_valid():
            return form.save()

        raise ValidationError(
            f"{self.form_class.__name__} is invalid; couldn't be saved! {form.errors.as_data()}"
        )

    def get_known_from_fields(self):
        """Return set of all known from_fields, including aliases thereof"""

        return {
            from_field
            for field_map in self.field_maps
            for from_field in list(field_map.aliases.keys()) + field_map.from_fields
        }

    def get_known_to_fields(self):
        return {
            to_field
            for field_map in self.field_maps
            for to_field in field_map.to_fields
        }

    def __repr__(self):
        field_maps_str = "\n  ".join([str(field_map) for field_map in self.field_maps])
        return f"FormMap {{\n  {field_maps_str}\n}}"


class FieldMap:
    """Map a to_field to its associated from_fields, a converter function, and any aliases"""

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
        # aliases=None,
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

        # if aliases:
        #     self.aliases = self._invert_aliases(aliases)

        self.aliases = {from_field: from_field for from_field in self.from_fields}
        if isinstance(self.from_fields, dict):
            self.aliases.update(self._invert_aliases(self.from_fields))
            self.from_fields = list(self.from_fields.keys())

        if not self.from_fields:
            raise ValueError("Either from_field or from_fields must be provided!")
        # print("aliases", self.aliases)

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

    @staticmethod
    def _invert_aliases(fields_to_aliases):
        """Given dict of {field: aliases}, return dict of {alias: field}

        For example, if fields_to_aliases={
            "latitude": ("LAT", "lat."), "longitude": ("LONG", "long.")
        }, then we return:
        {
            'LAT': 'latitude',
            'lat.': 'latitude',
            'LONG': 'longitude',
            'long.': 'longitude'
        }
        """
        return {
            alias: field
            for field, aliases in fields_to_aliases.items()
            for alias in aliases
        }

    def __repr__(self):
        if len(self.from_fields) == 1:
            from_ = "1"
            try:
                from_fields = self.from_fields[0]
            except KeyError:
                from_fields = next(iter(self.from_fields.keys()))
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
            unmapped_from_fields = [key for key in kwargs if key not in self.aliases]
            if unmapped_from_fields:
                raise ValueError(
                    f"Found fields {unmapped_from_fields} with no known alias. "
                    f"Known aliases: {self.aliases}"
                )

        # print("kwargs", kwargs)
        ret = {self.aliases.get(key, key): value for key, value in kwargs.items()}
        # print("ret", ret)
        if not ret:
            # print(f"WARNING: Failed to produce value for {kwargs}")
            return {}
        # Handle the simple 1:1/n:1 cases here to save on boilerplate externally
        # That is, allow for the existence of converters that don't return
        # {to_field: converted values} dicts, and instead simply return
        # converted values
        if self.map_type in (self.ONE_TO_ONE, self.MANY_TO_ONE):
            to_field = self.to_fields[0]
            if self.map_type == self.MANY_TO_ONE:
                converted = self.converter(**ret)
                if not isinstance(converted, dict):
                    return {to_field: converted}
                return converted

            from_field_value = next(iter(ret.values()))
            return {to_field: self.converter(from_field_value)}

        # For all other cases, expect the converter to be smart enough
        return self.converter(**ret)
