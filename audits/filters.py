import django_filters

from django_import_data.models import (
    ModelImportAttempt,
    FileImporter,
    FileImportAttempt,
    RowData,
)

from cases.filters import HelpedFilterSet
from utils.layout import discover_fields


from .form_helpers import (
    FileImportAttemptFilterFormHelper,
    FileImporterFilterFormHelper,
    ModelImportAttemptFilterFormHelper,
    RowDataFilterFormHelper,
)


class ModelImportAttemptFilter(HelpedFilterSet):
    class Meta:
        model = ModelImportAttempt
        formhelper_class = ModelImportAttemptFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class FileImporterFilter(HelpedFilterSet):
    class Meta:
        model = FileImporter
        formhelper_class = FileImporterFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class FileImportAttemptFilter(HelpedFilterSet):
    class Meta:
        model = FileImportAttempt
        formhelper_class = FileImportAttemptFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class RowDataFilter(HelpedFilterSet):
    # audit_groups = django_filters.ChoiceFilter(lookup_expr="models")

    class Meta:
        model = RowData
        formhelper_class = RowDataFilterFormHelper
        fields = discover_fields(formhelper_class.layout)
