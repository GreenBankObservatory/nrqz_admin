"""Audits Table definitions"""

import django_tables2 as tables
from django_import_data.models import (
    GenericAudit,
    GenericAuditGroup,
    GenericAuditGroupBatch,
    GenericBatchImport,
    RowData,
)

from .filters import (
    GenericAuditFilter,
    GenericAuditGroupBatchFilter,
    GenericAuditGroupFilter,
    GenericBatchImportFilter,
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


class GenericAuditGroupBatchTable(tables.Table):
    id = tables.Column(linkify=True)
    imports = tables.Column(linkify=True, verbose_name="Batch Imports")
    status = AuditStatusColumn()

    class Meta:
        model = GenericAuditGroupBatch
        fields = GenericAuditGroupBatchFilter.Meta.fields

    def render_imports(self, value):
        batch_imports = value
        return sorted(
            batch_imports.values_list(
                "genericauditgroup_audit_groups__form_map", flat=True
            ).distinct()
        )


class GenericBatchImportTable(tables.Table):
    id = tables.Column(linkify=True)
    audit_groups = tables.Column()
    status = AuditStatusColumn()

    class Meta:
        model = GenericBatchImport
        fields = GenericBatchImportFilter.Meta.fields

    def render_id(self, record):
        return f"Import {record.id}: {record.name}"

    # def render_imported_from(self, record):
    #     os.basename()
    #     return audit_groups.values("form_map").distinct()
    def render_audit_groups(self, value):
        audit_groups = value
        return list(audit_groups.values_list("importee_class", flat=True).distinct())


class GenericAuditGroupTable(tables.Table):
    id = tables.Column(linkify=True, verbose_name="Importer")
    status = AuditStatusColumn()

    class Meta:
        model = GenericAuditGroup
        fields = GenericAuditGroupFilter.Meta.fields

    def render_id(self, record):
        return str(record)


class GenericAuditTable(tables.Table):
    id = tables.Column(linkify=True)
    status = AuditStatusColumn()

    class Meta:
        model = GenericAudit
        fields = GenericAuditFilter.Meta.fields


class RowDataTable(tables.Table):
    id = tables.Column(linkify=True, verbose_name="ID")
    audit_groups = ImportStatusColumn()

    class Meta:
        model = RowData
        # Remove genericauditgroup_audit_groups__status and replace it with audit_groups
        fields = [
            *[
                field
                for field in RowDataFilter.Meta.fields
                if field != "genericauditgroup_audit_groups__status"
            ],
            "audit_groups",
        ]
        # fields = (*RowDataFilter.Meta.fields, "audit_groups")

    def render_id(self, record):
        return f"Row data for models: {record.get_audited_models()}"
