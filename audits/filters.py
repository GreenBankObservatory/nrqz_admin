import django_filters

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
    is_active = django_filters.BooleanFilter(field_name="is_active", label="Active")

    class Meta:
        model = FileImportBatch
        formhelper_class = FileImportBatchFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class FileImporterFilter(HelpedFilterSet):
    last_imported_path = django_filters.CharFilter(lookup_expr="icontains")
    acknowledged = django_filters.BooleanFilter(
        field_name="file_import_attempts__acknowledged", initial=False
    )

    class Meta:
        model = FileImporter
        formhelper_class = FileImporterFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class FileImportAttemptFilter(HelpedFilterSet):
    imported_from = django_filters.CharFilter(lookup_expr="icontains")
    acknowledged = django_filters.BooleanFilter(initial=False)

    class Meta:
        model = FileImportAttempt
        formhelper_class = FileImportAttemptFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class ModelImportAttemptFilter(HelpedFilterSet):
    class Meta:
        model = ModelImportAttempt
        formhelper_class = ModelImportAttemptFilterFormHelper
        fields = discover_fields(formhelper_class.layout)
