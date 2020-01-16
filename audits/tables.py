"""Audits Table definitions"""

from django.conf import settings

import django_tables2 as tables
from django_import_data.models import (
    ModelImporter,
    ModelImportAttempt,
    FileImporter,
    FileImportAttempt,
    FileImporterBatch,
    RowData,
)
from django_import_data.utils import to_fancy_str

from cases.columns import RemappedUnboundFileColumn
from .filters import (
    ModelImporterFilter,
    ModelImportAttemptFilter,
    FileImporterFilter,
    FileImportAttemptFilter,
    FileImporterBatchFilter,
    RowDataFilter,
)
from .columns import (
    BaseNameColumn,
    ImportStatusColumn,
    CurrentStatusColumn,
    TitledCheckBoxColumn,
    JsonColumn,
)
from utils.spec import parse_importer_spec, SPEC_FILE


class FileImporterBatchTable(tables.Table):
    id = tables.Column(linkify=True, verbose_name="FIB")
    command = tables.Column(verbose_name="Importer")
    created_on = tables.DateTimeColumn(verbose_name="Date Imported")
    status = ImportStatusColumn()
    # current_status = CurrentStatusColumn()
    num_file_importers = tables.Column(
        verbose_name="# Files",
        attrs={"th": {"title": "The number of File Importers in this batch"}},
    )
    num_successful_file_importers = tables.Column(
        verbose_name="# Successful Files",
        attrs={
            "th": {
                "title": "The number of File Importers in this batch that were successfully imported"
            }
        },
    )
    num_failed_file_importers = tables.Column(
        verbose_name="# Failed Files",
        attrs={
            "th": {
                "title": "The number of File Importers in this batch that were not successfully imported"
            }
        },
    )

    class Meta:
        model = FileImporterBatch
        fields = (
            FileImporterBatchFilter.Meta.fields[0],
            "command",
            *FileImporterBatchFilter.Meta.fields[1:],
        )

    def render_id(self, value):
        return f"FIB {value}"


class FileImporterTable(tables.Table):
    id = tables.Column(linkify=True, verbose_name="FI")
    file_path = RemappedUnboundFileColumn()
    status = ImportStatusColumn(
        verbose_name="Import Status",
        attrs={
            "th": {
                "title": "The most severe status out of all File Import "
                "Attempts in the history of this Importer"
            }
        },
    )
    current_status = CurrentStatusColumn()
    num_file_import_attempts = tables.Column(
        verbose_name="# FIAs",
        attrs={"th": {"title": "The number of FIAs that this FI has created"}},
    )
    num_model_importers = tables.Column(
        verbose_name="# MIs",
        attrs={"th": {"title": "The number of MIs in this FI's most recent FIA"}},
    )

    class Meta:
        model = FileImporter
        fields = FileImporterFilter.Meta.fields

    def render_id(self, value):
        return f"FI {value}"


class FileImporterSummaryTable(tables.Table):
    id = tables.Column(linkify=True, verbose_name="FI")
    # TODO: This should not be hardcoded here; this really should be table driven somehow...
    file_path = RemappedUnboundFileColumn(basename=True, verbose_name="Open File")
    status = ImportStatusColumn(
        verbose_name="Import Status",
        attrs={
            "th": {
                "title": "The most severe status out of all File Import "
                "Attempts in the history of this Importer"
            }
        },
    )
    current_status = CurrentStatusColumn()

    class Meta:
        model = FileImporter
        fields = FileImporterFilter.Meta.fields

    def render_id(self, value):
        return f"FI {value}"


class FileImporterDashboardTable(FileImporterTable):
    check = TitledCheckBoxColumn(
        accessor="id",
        attrs={
            "th": {
                "title": "Select the FIs you want to affect (or the checkbox here to affect all of them)"
            },
            "th__input": {"title": "Select all", "name": "all"},
        },
        verbose_name="Select",
    )

    class Meta:
        model = FileImporter
        fields = [
            field
            for field in FileImporterFilter.Meta.fields
            if field not in "acknowledged"
        ]
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
    current_status = CurrentStatusColumn()
    imported_from = RemappedUnboundFileColumn()

    num_model_importers = tables.Column(
        verbose_name="# MIs",
        attrs={
            "th": {
                "title": "The number of MIs that this FIA created (i.e. the number of models it tried to import)"
            }
        },
    )

    class Meta:
        model = FileImportAttempt
        fields = FileImportAttemptFilter.Meta.fields

    def render_id(self, value):
        return f"FIA {value}"


class RowDataTable(tables.Table):
    id = tables.Column(linkify=True, verbose_name="RD ID")
    status = ImportStatusColumn(
        verbose_name="Import Status",
        attrs={
            "th": {
                "title": "The most severe status out of all Model Import "
                "Attempts in the history of this Importer"
            }
        },
    )
    current_status = CurrentStatusColumn()
    num_model_importers = tables.Column(
        verbose_name="# MIs",
        attrs={"th": {"title": "The number of MIs created from this row"}},
    )

    class Meta:
        model = RowData
        fields = RowDataFilter.Meta.fields
        order_by = ["-status", "-modified_on"]

    def render_id(self, value):
        return f"RD {value}"

    def render_importee_field_data(self, record):
        return (
            record.model_importers.all()
            .annotate_latest_mia_importee_field_data()
            .values("latest_mia_importee_field_data")
        )

    def render_errors(self, record):
        return (
            record.model_importers.all()
            .annotate_latest_mia_errors()
            .values("latest_mia_errors")
        )


class ModelImporterTable(tables.Table):
    id = tables.Column(linkify=True, verbose_name="MI")
    status = ImportStatusColumn(
        verbose_name="Import Status",
        attrs={
            "th": {
                "title": "The most severe status out of all Model Import "
                "Attempts in the history of this Importer"
            }
        },
    )
    current_status = CurrentStatusColumn()
    num_model_import_attempts = tables.Column(
        verbose_name="# MIAs",
        attrs={"th": {"title": "The number of MIAs in this MI's most recent MIA"}},
    )
    row_data = tables.Column(linkify=True, verbose_name="Row Data")
    importee = tables.Column(
        linkify=True,
        # Can't order this because it isn't a real field
        orderable=False,
        verbose_name="Imported Model",
        accessor="latest_model_import_attempt.importee",
        attrs={"th": {"title": "The model, if any, that was ACTUALLY created"}},
    )
    errors = tables.Column(empty_values=(), verbose_name="Fields with Errors")

    class Meta:
        model = ModelImporter
        fields = ModelImporterFilter.Meta.fields
        order_by = ["-status", "-modified_on"]

    def render_id(self, value):
        return f"MI {value}"

    def render_errors(self, record):
        if record.latest_model_import_attempt.errors:
            return to_fancy_str(
                record.latest_model_import_attempt.gen_error_summary(), quote=True
            )

        return "—"


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
    status = ImportStatusColumn(
        verbose_name="MIA Status",
        attrs={"th": {"title": "The status of the import attempted for THIS MODEL"}},
    )
    current_status = CurrentStatusColumn()
    row_data = tables.Column(linkify=True, verbose_name="Row Data")
    error_summary = tables.Column(verbose_name="Fields with Errors")

    class Meta:
        model = ModelImportAttempt
        fields = [
            *ModelImportAttemptFilter.Meta.fields[:3],
            "importee",
            *ModelImportAttemptFilter.Meta.fields[3:],
        ]
        order_by = ["-created_on"]

    def render_id(self, value):
        return f"MIA {value}"

    def render_importee(self, record):
        return str(record.importee)

    def render_error_summary(self, record):
        return to_fancy_str(record.gen_error_summary(), quote=True)


class ModelImportAttemptFailureTable(ModelImportAttemptTable):
    errors = JsonColumn()
    importee_field_data = JsonColumn()

    class Meta(ModelImportAttemptTable.Meta):
        exclude = ["current_status", "importee", "error_summary"]


class FileImporterErrorSummaryTable(tables.Table):
    row_nums = tables.Column(verbose_name="Row #s")
    aliases = tables.Column(verbose_name="From Fields")
    error = tables.Column(verbose_name="Errors")


class UnimportedFilesDashboardTable(tables.Table):
    file_paths = tables.TemplateColumn(
        verbose_name="Path Groups",
        template_name="audits/paths_column.html",
        attrs={
            "th": {
                "title": "Each row here contains all files that have exactly the "
                "same contents (same hash)"
            }
        },
    )
    importer = tables.TemplateColumn(
        template_name="audits/importer_column.html",
        extra_context={"importers": list(parse_importer_spec(SPEC_FILE).keys())},
        attrs={
            "th": {
                "title": "The importer to use for importing. The correct one has almost certainly "
                "been automatically selected, but you can change it if you need to."
            }
        },
    )

    check = TitledCheckBoxColumn(
        empty_values=(),
        accessor="file_hash",
        attrs={
            "th": {
                "title": "Select the files you want to affect (or the checkbox here to affect all of them)"
            },
            "th__input": {"title": "Select all", "name": "all"},
        },
        verbose_name="Select",
    )


class OrphanedFilesDashboardTable(tables.Table):
    file_import_attempt = tables.Column(
        linkify=True, accessor="imported_from", verbose_name="FIA Path (Path on Disk)"
    )
    file_importer = tables.Column(
        linkify=True,
        accessor="file_importer.file_path",
        verbose_name="File Importer Path",
    )
    is_on_disk = tables.Column(verbose_name="FIA Path Exists on Disk")

    class Meta:
        model = FileImportAttempt
        fields = ("file_import_attempt", "file_importer", "is_on_disk")


class FileImportAttemptSummaryTable(tables.Table):
    model_class = tables.Column()
    instance = tables.Column(linkify=True)
    row_data = tables.Column(
        accessor="instance.model_import_attempt.model_importer.row_data", linkify=True
    )
    model_import_attempt = tables.Column(
        accessor="instance.model_import_attempt", linkify=True
    )

    def render_row_data(self, value):
        return f"Row {value.row_num}"
