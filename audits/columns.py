"""Audits Column definitions"""

import os

from django.utils.html import escape
from django.utils.safestring import mark_safe

from django_tables2 import Column, CheckBoxColumn, TemplateColumn
from django_import_data.mixins import ImportStatusModel, CurrentStatusModel


class _StatusColumn(Column):
    def render(self, value):
        # Handle both DB value AND named value
        try:
            status = self.STATUSES[int(value)]
        except ValueError:
            status = self.STATUSES[value]

        title, css_class = self.derive_from_status(status)

        value = escape(value)
        display = status.value
        return mark_safe(f"<span title='{title}'' class='{css_class}'>{display}</span>")


class ImportStatusColumn(_StatusColumn):
    """Column for colorizing Audit status values"""

    STATUSES = ImportStatusModel.STATUSES

    def derive_from_status(self, status):
        if status == self.STATUSES.rejected:
            title = "One or more model import attempts were rejected"
            css_class = "batch-rejected"
        elif status == self.STATUSES.created_dirty:
            title = "One or more model import attempts were imported with some errors"
            css_class = "batch-created_dirty"
        elif status == self.STATUSES.created_clean:
            title = "All model import attempts were imported cleanly"
            css_class = "batch-created_clean"
        elif status == self.STATUSES.pending:
            title = "Import is in progress"
            css_class = "batch-pending"
        elif status == self.STATUSES.empty:
            title = "No model imports were attempted"
            css_class = "batch-rejected"
        else:
            raise ValueError(
                f"{self.__class__.__name__} got unexpected value: {value!r}"
            )

        return title, css_class


class CurrentStatusColumn(_StatusColumn):
    """Column for colorizing Audit status values"""

    STATUSES = CurrentStatusModel.CURRENT_STATUSES

    def derive_from_status(self, status):
        if status == self.STATUSES.deleted:
            title = "All created models have been deleted"
            css_class = "batch-created_dirty"
        elif status == self.STATUSES.acknowledged:
            title = "Has been acknowledged"
            css_class = "batch-created_clean"
        elif status == self.STATUSES.active:
            title = "No model imports were attempted"
            css_class = "batch-pending"
        else:
            raise ValueError(
                f"{self.__class__.__name__} got unexpected value: {value!r}"
            )

        return title, css_class


class BaseNameColumn(Column):
    def render(self, value):
        return mark_safe(f"<span title='{value}'>{os.path.basename(value)}</span>")


class TitledCheckBoxColumn(CheckBoxColumn):
    @property
    def header(self):
        return mark_safe(f"<span>{self.verbose_name} {super().header}</span>")


class JsonColumn(TemplateColumn):
    def __init__(self, *args, **kwargs):
        template_name = "audits/json_column.html"

        super().__init__(*args, template_name=template_name, **kwargs)
