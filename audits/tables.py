"""Audits Table definitions"""

import django_tables2 as tables
from django_import_data.models import (
    ModelImportAttempt,
    FileImporter,
    FileImportAttempt,
    RowData,
)

from .filters import (
    ModelImportAttemptFilter,
    FileImporterFilter,
    FileImportAttemptFilter,
    RowDataFilter,
)
from .columns import AuditStatusColumn


def clean_batch_name(value):
    prefix = "stripped_data_only_"
    if value.startswith(prefix):
        return value[len(prefix) :].replace("_", " ")
    return value


class ImportStatusColumn(tables.Column):
    def render(self, value):
        status_models = value
        return {model.name: model.status for model in status_models.all()}


class FileImporterTable(tables.Table):
    id = tables.Column(linkify=True)
    # imports = tables.Column(linkify=True, verbose_name="Batch Imports")
    status = AuditStatusColumn()

    class Meta:
        model = FileImportAttempt
        fields = FileImportAttemptFilter.Meta.fields

    # def render_imports(self, value):
    #     batch_imports = value
    #     return sorted(
    #         batch_imports.values_list(
    #             "genericauditgroup_audit_groups__form_map", flat=True
    #         ).distinct()
    #     )


class FileImportAttemptTable(tables.Table):
    id = tables.Column(linkify=True)
    # imports = tables.Column(linkify=True, verbose_name="Batch Imports")
    status = AuditStatusColumn()

    class Meta:
        model = FileImporter
        fields = FileImporterFilter.Meta.fields

    # def render_imports(self, value):
    #     batch_imports = value
    #     return sorted(
    #         batch_imports.values_list(
    #             "genericauditgroup_audit_groups__form_map", flat=True
    #         ).distinct()
    #     )


class ModelImportAttemptTable(tables.Table):
    id = tables.Column(linkify=True)
    status = AuditStatusColumn()

    class Meta:
        model = ModelImportAttempt
        fields = ModelImportAttemptFilter.Meta.fields


class RowDataTable(tables.Table):
    id = tables.Column(linkify=True, verbose_name="ID")
    # audit_groups = ImportStatusColumn()

    class Meta:
        model = RowData
        fields = RowDataFilter.Meta.fields

    def render_id(self, record):
        return f"Row data for models: {record.get_audited_models()}"
