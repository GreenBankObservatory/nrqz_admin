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
from .columns import BaseNameColumn, ImportStatusColumn, TitledCheckBoxColumn


class FileImportBatchTable(tables.Table):
    id = tables.Column(linkify=True, verbose_name="FIB")
    command = tables.Column(verbose_name="Importer")
    created_on = tables.DateTimeColumn(verbose_name="Date Imported")
    status = ImportStatusColumn()
    num_file_import_attempts = tables.Column(
        verbose_name="# FIAs",
        attrs={
            "th": {
                "title": "The number of MIAs that this FIA created (i.e. the number of models it tried to import)"
            }
        },
    )

    class Meta:
        model = FileImportBatch
        fields = (
            FileImportBatchFilter.Meta.fields[0],
            "command",
            *FileImportBatchFilter.Meta.fields[1:],
        )

    def render_id(self, value):
        return f"FIB {value}"


class FileImporterTable(tables.Table):
    id = tables.Column(linkify=True, verbose_name="FI")
    file_path = BaseNameColumn()
    status = ImportStatusColumn(
        verbose_name="Import Status",
        attrs={
            "th": {
                "title": "The most severe status out of all File Import "
                "Attempts in the history of this Importer"
            }
        },
    )
    acknowledged = tables.BooleanColumn()
    num_file_import_attempts = tables.Column(
        verbose_name="# FIAs",
        attrs={"th": {"title": "The number of FIAs that this FI has created"}},
    )
    num_model_import_attempts = tables.Column(
        verbose_name="# MIAs",
        attrs={"th": {"title": "The number of MIAs in this FI's most recent FIA"}},
    )

    class Meta:
        model = FileImporter
        fields = FileImporterFilter.Meta.fields
        order_by = ["-modified_on"]

    def render_id(self, value):
        return f"FI {value}"


class FileImporterDashboardTable(FileImporterTable):
    check = TitledCheckBoxColumn(
        accessor="id",
        attrs={
            "th": {
                "title": "Select the FIs you want to acknowledged (or the checkbox here to acknowledge all of them)"
            },
            "th__input": {"title": "Acknowledge all", "name": "all"},
        },
        verbose_name="Acknowledge",
    )

    class Meta:
        model = FileImporter
        fields = FileImporterFilter.Meta.fields
        order_by = ["-modified_on"]


class FileImportAttemptTable(tables.Table):
    id = tables.Column(linkify=True, verbose_name="FIA")
    status = ImportStatusColumn(
        verbose_name="Import Status",
        # attrs={
        #     "th": {
        #         "title": "The most severe status out of all model import "
        #         "attempts made from this file"
        #     }
        # },
    )
    imported_from = BaseNameColumn()

    num_model_import_attempts = tables.Column(
        verbose_name="# MIAs",
        attrs={
            "th": {
                "title": "The number of MIAs that this FIA created (i.e. the number of models it tried to import)"
            }
        },
    )

    class Meta:
        model = FileImportAttempt
        fields = FileImportAttemptFilter.Meta.fields

    def render_id(self, value):
        return f"FIA {value}"


class ModelImportAttemptTable(tables.Table):
    id = tables.Column(linkify=True, verbose_name="MIA")
    created_on = tables.DateTimeColumn(verbose_name="Imported On")
    importee = tables.Column(
        linkify=True,
        # Can't order this because it isn't a real field
        orderable=False,
        verbose_name="Imported Model",
        attrs={"th": {"title": "The model, if any, that was ACTUALLY created"}},
    )
    content_type = tables.Column(
        verbose_name="Model",
        attrs={"th": {"title": "The model that the importer ATTEMPTED to create"}},
    )
    fia_imported_from = tables.Column(
        linkify=True, accessor="file_import_attempt.imported_from"
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
        ]
        order_by = ["-created_on"]

    def render_id(self, value):
        return f"MIA {value}"

    def render_fia_imported_from(self, value):
        return os.path.basename(value)

    def render_importee(self, record):
        return str(record.importee)
