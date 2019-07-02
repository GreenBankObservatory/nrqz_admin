import django_filters

from django import forms

from django_import_data.models import (
    FileImportAttempt,
    FileImporter,
    ModelImportAttempt,
    FileImportBatch,
)

from cases.filters import HelpedFilterSet
from utils.layout import discover_fields

from .form_helpers import (
    FileImportAttemptFilterFormHelper,
    FileImporterFilterFormHelper,
    ModelImportAttemptFilterFormHelper,
    FileImportBatchFilterFormHelper,
)


class FileImportBatchFilter(HelpedFilterSet):
    id = django_filters.NumberFilter(label="File Import Batch ID")
    status = django_filters.ChoiceFilter(
        label="Import Status", choices=ModelImportAttempt.STATUSES.as_filter_choices()
    )
    created_on = django_filters.DateFromToRangeFilter()

    class Meta:
        model = FileImportBatch
        formhelper_class = FileImportBatchFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class FileImporterFilter(HelpedFilterSet):
    id = django_filters.NumberFilter(label="File Importer ID")
    file_path = django_filters.CharFilter(lookup_expr="icontains")
    acknowledged = django_filters.BooleanFilter(
        label="Acknowledged",
        # field_name="file_import_attempts__acknowledged",
        initial=False,
    )
    status = django_filters.ChoiceFilter(
        label="Import Status", choices=ModelImportAttempt.STATUSES.as_filter_choices()
    )

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


class ModelImportAttemptFilter(HelpedFilterSet):
    id = django_filters.NumberFilter(label="Model Import Attempt ID")

    class Meta:
        model = ModelImportAttempt
        formhelper_class = ModelImportAttemptFilterFormHelper
        fields = discover_fields(formhelper_class.layout)
