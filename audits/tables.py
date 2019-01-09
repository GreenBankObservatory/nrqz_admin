"""Audits Table definitions"""

import os

from django.utils.safestring import mark_safe

import django_tables2 as tables
from django_import_data.models import RowData

from . import models
from .filters import BatchAuditFilter, BatchAuditGroupFilter, RowDataFilter
from .columns import AuditStatusColumn


def clean_batch_name(value):
    prefix = "stripped_data_only_"
    if value.startswith(prefix):
        return value[len(prefix) :].replace("_", " ")
    return value


class BatchAuditTable(tables.Table):
    original_file = tables.Column(linkify=True, verbose_name="Path")
    status = AuditStatusColumn()

    class Meta:
        model = models.BatchAudit
        fields = BatchAuditFilter.Meta.fields

    def render_original_file(self, value):
        # TODO: Remove lstrip
        return mark_safe(f"Batch {clean_batch_name(os.path.basename(value))}")


class BatchAuditGroupTable(tables.Table):
    last_imported_path = tables.Column(linkify=True, verbose_name="Name")
    batch = tables.Column(linkify=True)
    status = AuditStatusColumn()

    class Meta:
        model = models.BatchAuditGroup
        fields = BatchAuditGroupFilter.Meta.fields

    def render_last_imported_path(self, value):
        batch_name = clean_batch_name(os.path.basename(value))
        return mark_safe(batch_name)

    def render_batch(self, value):
        return f"Batch {clean_batch_name(str(value))}"


class AuditGroupStatusColumn(tables.Column):
    def render(self, value):
        audit_groups = value
        return {ag.name: ag.status for ag in audit_groups.all()}


class RowDataTable(tables.Table):
    id = tables.Column(linkify=True, verbose_name="ID")
    audit_groups = AuditGroupStatusColumn()

    class Meta:
        model = RowData
        # Remove audit_groups__status and replace it with audit_groups
        fields = [
            *[
                field
                for field in RowDataFilter.Meta.fields
                if field != "audit_groups__status"
            ],
            "audit_groups",
        ]
        # fields = (*RowDataFilter.Meta.fields, "audit_groups")

    def render_id(self, record):
        return f"Row data for models: {record.get_audited_models()}"
