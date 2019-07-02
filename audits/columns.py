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
            title = "One or more model import attempts were rejected"
            css_class = "batch-rejected"
        elif status == STATUSES.created_dirty:
            title = "One or more model import attempts were imported with some errors"
            css_class = "batch-created_dirty"
        elif status == STATUSES.created_clean:
            title = "All model import attempts were imported cleanly"
            css_class = "batch-created_clean"
        elif status == STATUSES.pending:
            title = "Import is in progress"
            css_class = "batch-pending"
        elif status == STATUSES.deleted:
            title = "All associated models have been deleted"
            css_class = "batch-pending"
        elif status == STATUSES.empty:
            title = "No model imports were attempted"
            css_class = "batch-rejected"
        else:
            raise ValueError(f"ImportStatusColumn got unexpected value: {value!r}")

        value = escape(value)
        display = status.value
        return mark_safe(f"<span title='{title}'' class='{css_class}'>{display}</span>")


class BaseNameColumn(Column):
    def render(self, value):
        return mark_safe(f"<span title='{value}'>{os.path.basename(value)}</span>")
