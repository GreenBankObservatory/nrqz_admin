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
    status = AuditStatusColumn()

    class Meta:
        model = GenericAuditGroupBatch
        fields = GenericAuditGroupBatchFilter.Meta.fields

    # def render_original_file(self, value):
    #     # TODO: Remove lstrip
    #     return mark_safe(f"Batch {clean_batch_name(os.path.basename(value))}")


class GenericBatchImportTable(tables.Table):
    id = tables.Column(linkify=True)
    status = AuditStatusColumn()

    class Meta:
        model = GenericBatchImport
        fields = GenericBatchImportFilter.Meta.fields

    # def render_last_imported_path(self, value):
    #     batch_name = clean_batch_name(os.path.basename(value))
    #     return mark_safe(batch_name)

    # def render_batch(self, value):
    #     return f"Batch {clean_batch_name(str(value))}"


class GenericAuditGroupTable(tables.Table):
    id = tables.Column(linkify=True)
    status = AuditStatusColumn()

    class Meta:
        model = GenericAuditGroup
        fields = GenericAuditGroupFilter.Meta.fields

    def render_content_type(self, record):
        if record.auditee:
            auditee_str = str(record.auditee)
        else:
            auditee_str = "<Failed to create>"
        return f"{record.content_type}: {auditee_str}"


class GenericAuditTable(tables.Table):
    id = tables.Column(linkify=True)
    status = AuditStatusColumn()

    class Meta:
        model = GenericAudit
        fields = GenericAuditFilter.Meta.fields

    def render_content_type(self, record):
        if record.audit_group.auditee:
            auditee_str = str(record.audit_group.auditee)
        else:
            auditee_str = "<Failed to create>"
        return f"{record.audit_group.content_type}: {auditee_str}"


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
