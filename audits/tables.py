import os

import django_tables2 as tables
from django.utils.safestring import mark_safe

from . import models
from .filters import BatchAuditFilter, BatchAuditGroupFilter


class BatchAuditTable(tables.Table):
    original_file = tables.Column(linkify=True, verbose_name="Batch Audit")

    class Meta:
        model = models.BatchAudit
        fields = BatchAuditFilter.Meta.fields

    def render_original_file(self, value):
        return mark_safe(os.path.basename(value))


class BatchAuditGroupTable(tables.Table):
    id = tables.Column(linkify=True)
    batch = tables.Column(linkify=True)

    class Meta:
        model = models.BatchAuditGroup
        fields = BatchAuditGroupFilter.Meta.fields
