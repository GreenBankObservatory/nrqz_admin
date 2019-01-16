"""Audits Table definitions"""
import os

import django_tables2 as tables
from django_import_data.models import (
    ModelImportAttempt,
    FileImporter,
    FileImportAttempt,
)

from .filters import (
    ModelImportAttemptFilter,
    FileImporterFilter,
    FileImportAttemptFilter,
)
from .columns import ImportStatusColumn


class FileImporterTable(tables.Table):
    id = tables.Column(linkify=True)
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

    class Meta:
        model = FileImporter
        fields = FileImporterFilter.Meta.fields

    def render_last_imported_path(self, value):
        return os.path.basename(value)


class FileImportAttemptTable(tables.Table):
    id = tables.Column(linkify=True)
    imported_from = tables.Column(linkify=True)
    status = ImportStatusColumn()

    class Meta:
        model = FileImportAttempt
        fields = FileImportAttemptFilter.Meta.fields

    def render_imported_from(self, value):
        return os.path.basename(value)


class ModelImportAttemptTable(tables.Table):
    id = tables.Column(linkify=True)
    # Can't order this because it isn't a real field
    importee = tables.Column(linkify=True, empty_values=(), orderable=False)
    created_on = tables.DateTimeColumn(verbose_name="Imported On")
    content_type = tables.Column(verbose_name="Model")
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
