"""Audits Column definitions"""

from django.utils.html import escape
from django.utils.safestring import mark_safe

from django_tables2 import Column


class AuditStatusColumn(Column):
    """Column for colorizing Audit status values"""

    def render(self, value):
        # TODO: Consolidate these definitions
        if value == "Rejected: Fatal Errors":
            css_class = "batch-rejected"
        elif value == "Imported: Some Errors":
            css_class = "batch-created_dirty"
        elif value == "Imported: No Errors":
            css_class = "batch-created_clean"
        elif value == "Pending":
            css_class = "batch-pending"
        else:
            raise ValueError(f"Invalid value: {value}")
        value = escape(value)
        return mark_safe(f"<span class='{css_class}'>{value}</span>")
