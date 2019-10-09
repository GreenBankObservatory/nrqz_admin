"""Custom djang_tables2.Column sub-classes for cases app"""
import os
import re

from django.utils.html import escape
from django.utils.safestring import mark_safe

from django_tables2 import CheckBoxColumn, Column
from django_tables2.utils import AttributeDict

from utils.misc import to_file_link


class TrimmedTextColumn(Column):
    def __init__(self, *args, length=80, **kwargs):
        super(TrimmedTextColumn, self).__init__(*args, **kwargs)
        self.trim_length = length

    def render(self, value):
        value = escape(value)
        # first_line = value.split("\n")[0]
        if len(value) > self.trim_length:
            # trimmed = " ".join(first_line[: self.trim_length].split(" ")[:-1])
            trimmed = " ".join(value[: self.trim_length].split(" ")[:-1])
            if len(value) > 512:
                abs_trimmed = " ".join(value[:512].split(" ")[:-1]) + " ..."
            else:
                abs_trimmed = value
            return mark_safe(f"<span title='{abs_trimmed}'>{trimmed} ...</span>")
        return value

    def value(self, value):
        return value


class SelectColumn(CheckBoxColumn):
    verbose_name = "Select/Print"
    empty_values = ()

    def __init__(self, *args, **kwargs):
        super(SelectColumn, self).__init__(*args, **kwargs)

    @property
    def header(self):
        return mark_safe(f"<span>{SelectColumn.verbose_name}</span>")

    def render(self, value, bound_column, record):
        attrs = AttributeDict(
            {"type": "checkbox", "name": "facilities", "value": record.id}
        )
        return mark_safe("<input %s/>" % attrs.as_html())


class UnboundFileColumn(Column):
    def __init__(self, *args, text=None, **kwargs):
        if text:
            self.text = text
        else:
            self.text = None
        super().__init__(*args, **kwargs)

    def render(self, value, bound_column, record):
        path = value
        record.refresh_from_filesystem()

        # TODO: Fix this so that it is relative to the client, and not the
        # server, and it might actually be useful!
        # if record.file_missing:
        #     return "File does not exist"
        foo = f"""<a
href='{to_file_link(path)}'
title="{path}"
>
    {self.text if self.text else path}
</a>"""
        return mark_safe(foo)


class RemappedUnboundFileColumn(UnboundFileColumn):
    def __init__(self, remap_regex, replacement_str, *args, text=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.remap_regex = re.compile(remap_regex)
        self.replacement_str = replacement_str

    def render(self, value, bound_column, record):
        return super().render(
            self.remap_regex.sub(self.replacement_str, value).replace("/", "\\"),
            bound_column,
            record,
        )
