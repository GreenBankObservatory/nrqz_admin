import django_filters

from django_import_data.models import (
    FileImportAttempt,
    FileImporterBatch,
    FileImporter,
    ModelImportAttempt,
    ModelImporter,
    RowData,
)

from cases.filters import HelpedFilterSet
from utils.layout import discover_fields

from .form_helpers import (
    FileImportAttemptFilterFormHelper,
    FileImporterBatchFilterFormHelper,
    FileImporterFilterFormHelper,
    ModelImportAttemptFilterFormHelper,
    ModelImporterFilterFormHelper,
    RowDataFilterFormHelper,
)


class FileImporterBatchFilter(HelpedFilterSet):
    id = django_filters.NumberFilter(label="File Importer Batch ID")
    status = django_filters.ChoiceFilter(
        label="Import Status", choices=ModelImportAttempt.STATUSES.as_filter_choices()
    )
    created_on = django_filters.DateFromToRangeFilter()

    class Meta:
        model = FileImporterBatch
        formhelper_class = FileImporterBatchFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class FileImporterFilter(HelpedFilterSet):
    id = django_filters.NumberFilter(label="File Importer ID")
    file_path = django_filters.CharFilter(lookup_expr="icontains")
    acknowledged = django_filters.BooleanFilter(label="Acknowledged", initial=False)
    status = django_filters.ChoiceFilter(
        label="Import Status", choices=ModelImportAttempt.STATUSES.as_filter_choices()
    )
    last_imported = django_filters.DateFromToRangeFilter(label="Last Imported")

    class Meta:
        model = FileImporter
        formhelper_class = FileImporterFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class FileImportAttemptFilter(HelpedFilterSet):
    id = django_filters.NumberFilter(label="File Import Attempt ID")
    imported_from = django_filters.CharFilter(lookup_expr="icontains")
    acknowledged = django_filters.BooleanFilter(initial=False)
    status = django_filters.ChoiceFilter(
        label="Import Status", choices=ModelImportAttempt.STATUSES.as_filter_choices()
    )

    class Meta:
        model = FileImportAttempt
        formhelper_class = FileImportAttemptFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class RowDataFilter(HelpedFilterSet):
    id = django_filters.NumberFilter(label="Model Importer ID")
    status = django_filters.ChoiceFilter(
        label="Import Status", choices=ModelImportAttempt.STATUSES.as_filter_choices()
    )

    class Meta:
        model = RowData
        formhelper_class = RowDataFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class ModelImporterFilter(HelpedFilterSet):
    id = django_filters.NumberFilter(label="Model Importer ID")
    status = django_filters.ChoiceFilter(
        label="Import Status", choices=ModelImportAttempt.STATUSES.as_filter_choices()
    )
    row_data = None

    class Meta:
        model = ModelImporter
        formhelper_class = ModelImporterFilterFormHelper
        fields = [
            field
            for field in discover_fields(formhelper_class.layout)
            if field not in ["row_data"]
        ]


class ModelImportAttemptFilter(HelpedFilterSet):
    id = django_filters.NumberFilter(label="Model Import Attempt ID")

    class Meta:
        model = ModelImportAttempt
        formhelper_class = ModelImportAttemptFilterFormHelper
        fields = discover_fields(formhelper_class.layout)
