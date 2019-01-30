import django_filters

from django_import_data.models import (
    FileImportAttempt,
    FileImporter,
    ModelImportAttempt,
)

from cases.filters import HelpedFilterSet
from utils.layout import discover_fields

from .form_helpers import (
    FileImportAttemptFilterFormHelper,
    FileImporterFilterFormHelper,
    ModelImportAttemptFilterFormHelper,
)


class FileImporterFilter(HelpedFilterSet):
    last_imported_path = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = FileImporter
        formhelper_class = FileImporterFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class FileImportAttemptFilter(HelpedFilterSet):
    imported_from = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = FileImportAttempt
        formhelper_class = FileImportAttemptFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class ModelImportAttemptFilter(HelpedFilterSet):
    class Meta:
        model = ModelImportAttempt
        formhelper_class = ModelImportAttemptFilterFormHelper
        fields = discover_fields(formhelper_class.layout)
