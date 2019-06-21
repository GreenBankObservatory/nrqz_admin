"""Custom djang_tables2.Column sub-classes for cases app"""
import os

from django.utils.html import escape
from django.utils.safestring import mark_safe

from django_tables2 import Column, CheckBoxColumn, FileColumn
from django_tables2.utils import AttributeDict


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
        print("wtf")
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
    def render(self, value, bound_column, record):
        path = value
        # if not os.path.isfile(path):
        #     return "Broken Link"
        foo = f"""<a
href='file://{path}'
title={os.path.basename(path)}
>
    Open Attachment
</a>"""
        return mark_safe(foo)
