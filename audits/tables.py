import os

import django_tables2 as tables
from django.utils.safestring import mark_safe

from . import models
from .filters import BatchAuditFilter


class BatchAuditTable(tables.Table):
    original_file = tables.Column(linkify=True, verbose_name="Batch Audit")
    # linked_object = tables.Column(linkify=True, verbose_name="Batch")
    # created_on = tables.Column(verbose_name="Import Date")

    class Meta:
        model = models.BatchAudit
        fields = BatchAuditFilter.Meta.fields

    def render_original_file(self, value):
        return mark_safe(os.path.basename(value))
