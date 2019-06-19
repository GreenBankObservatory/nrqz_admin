"""Audits Column definitions"""

import os

from django.utils.html import escape
from django.utils.safestring import mark_safe

from django_tables2 import Column
from django_import_data.mixins import ImportStatusModel

STATUSES = ImportStatusModel.STATUSES


class ImportStatusColumn(Column):
    """Column for colorizing Audit status values"""

    def render(self, value):
        # Handle both DB value AND named value
        try:
            status = STATUSES[int(value)]
        except ValueError:
            status = STATUSES[value]

        if status == STATUSES.rejected:
            css_class = "batch-rejected"
        elif status == STATUSES.created_dirty:
            css_class = "batch-created_dirty"
        elif status == STATUSES.created_clean:
            css_class = "batch-created_clean"
        elif status == STATUSES.pending:
            css_class = "batch-pending"
        else:
            raise ValueError(f"ImportStatusColumn got unexpected value: {value!r}")

        value = escape(value)
        display = status.value
        return mark_safe(f"<span class='{css_class}'>{display}</span>")


class BaseNameColumn(Column):
    def render(self, value):
        return mark_safe(f"<span title='{value}'>{os.path.basename(value)}</span>")
