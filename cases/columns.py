from django.utils.html import escape
from django.utils.safestring import mark_safe

from django_tables2 import Column, CheckBoxColumn
from django_tables2.utils import AttributeDict


class TrimmedTextColumn(Column):
    def __init__(self, *args, length=80, **kwargs):
        super(TrimmedTextColumn, self).__init__(*args, **kwargs)
        self.trim_length = length

    def render(self, value):
        value = escape(value)
        first_line = value.split("\n")[0]
        if len(first_line) > self.trim_length:
            trimmed = " ".join(first_line[: self.trim_length].split(" ")[:-1])
            return mark_safe(f"<span title='{value[:512]}'>{trimmed} ...</span>")
        return first_line


class SelectColumn(CheckBoxColumn):
    verbose_name = "Concur"
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
