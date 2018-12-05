"""Audits Table definitions"""

import os

from django.utils.safestring import mark_safe

import django_tables2 as tables

from . import models
from .filters import BatchAuditFilter, BatchAuditGroupFilter
from .columns import AuditStatusColumn


class BatchAuditTable(tables.Table):
    original_file = tables.Column(linkify=True, verbose_name="Batch Audit")
    status = AuditStatusColumn()

    class Meta:
        model = models.BatchAudit
        fields = BatchAuditFilter.Meta.fields

    def render_original_file(self, value):
        return mark_safe(os.path.basename(value))


class BatchAuditGroupTable(tables.Table):
    id = tables.Column(linkify=True)
    batch = tables.Column(linkify=True)
    status = AuditStatusColumn()

    class Meta:
        model = models.BatchAuditGroup
        fields = BatchAuditGroupFilter.Meta.fields
