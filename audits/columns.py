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
        if value == STATUSES.rejected.value:
            css_class = "batch-rejected"
        elif value == STATUSES.created_dirty.value:
            css_class = "batch-created_dirty"
        elif value == STATUSES.created_clean.value:
            css_class = "batch-created_clean"
        elif value == STATUSES.pending.value:
            css_class = "batch-pending"
        else:
            raise ValueError(f"Invalid value: {value}")
        value = escape(value)
        return mark_safe(f"<span class='{css_class}'>{value}</span>")


class BaseNameColumn(Column):
    def render(self, value):
        return mark_safe(f"<span title='{value}'>{os.path.basename(value)}</span>")
