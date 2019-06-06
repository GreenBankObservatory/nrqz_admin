"""Audits Table definitions"""
import os

import django_tables2 as tables
from django_import_data.models import (
    ModelImportAttempt,
    FileImporter,
    FileImportAttempt,
    FileImportBatch,
)

from .filters import (
    ModelImportAttemptFilter,
    FileImporterFilter,
    FileImportAttemptFilter,
    FileImportBatchFilter,
)
from .columns import ImportStatusColumn


class FileImportBatchTable(tables.Table):
    command = tables.Column(empty_values=(), linkify=True, verbose_name="Importer")
    created_on = tables.DateColumn(verbose_name="Date Imported")
    file_import_attempts = tables.Column(verbose_name="# of File Imports Attempted")
    status = ImportStatusColumn()
    is_active = tables.BooleanColumn(verbose_name="Active")

    class Meta:
        model = FileImportBatch
        fields = ("command", *FileImportBatchFilter.Meta.fields)

    def render_file_import_attempts(self, value):
        return value.count()


class FileImporterTable(tables.Table):
    last_imported_path = tables.Column(linkify=True)
    status = ImportStatusColumn(
        verbose_name="Status",
        attrs={
            "th": {
                "title": "The most severe status out of all model import "
                "attempts made from this file"
            }
        },
    )
    acknowledged = tables.BooleanColumn()
    is_active = tables.BooleanColumn(verbose_name="Active")

    class Meta:
        model = FileImporter
        fields = FileImporterFilter.Meta.fields
        order_by = ["-modified_on"]

    def render_last_imported_path(self, value):
        return os.path.basename(value)


class FileImportAttemptTable(tables.Table):
    id = tables.DateColumn(linkify=True)
    imported_from = tables.Column(linkify=True)
    status = ImportStatusColumn()
    is_active = tables.BooleanColumn(verbose_name="Active")

    class Meta:
        model = FileImportAttempt
        fields = FileImportAttemptFilter.Meta.fields

    def render_imported_from(self, value):
        return os.path.basename(value)


class ModelImportAttemptTable(tables.Table):
    id = tables.Column(linkify=True, verbose_name="MIA")
    created_on = tables.DateTimeColumn(verbose_name="Imported On")
    # Can't order this because it isn't a real field
    importee = tables.Column(linkify=True, empty_values=(), orderable=False)
    content_type = tables.Column(
        verbose_name="Model",
        attrs={"th": {"title": "The model that the importer ATTEMPTED to create"}},
    )
    fia_imported_from = tables.Column(
        linkify=True, accessor="file_import_attempt.imported_from"
    )
    fia_status = ImportStatusColumn(
        accessor="file_import_attempt.status",
        verbose_name="File Import Attempt Status",
        attrs={
            "th": {
                "title": "The OVERALL status of the file import that this is a part of"
            }
        },
    )
    status = ImportStatusColumn(
        verbose_name="Model Import Attempt Status",
        attrs={"th": {"title": "The status of the import attempted for THIS MODEL"}},
    )

    class Meta:
        model = ModelImportAttempt
        fields = [
            *ModelImportAttemptFilter.Meta.fields[:3],
            "importee",
            *ModelImportAttemptFilter.Meta.fields[3:],
            "fia_imported_from",
            "fia_status",
        ]
        order_by = ["-created_on"]

    def render_fia_imported_from(self, value):
        return os.path.basename(value)

    def render_importee(self, record):
        return str(record.importee)
