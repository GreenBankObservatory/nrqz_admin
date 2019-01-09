import django_filters
from django_import_data.models import RowData

from cases.filters import HelpedFilterSet
from utils.layout import discover_fields

from . import models
from .form_helpers import (
    BatchAuditFilterFormHelper,
    BatchAuditGroupFilterFormHelper,
    RowDataFilterFormHelper,
)


class BatchAuditFilter(HelpedFilterSet):
    class Meta:
        model = models.BatchAudit
        formhelper_class = BatchAuditFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class BatchAuditGroupFilter(HelpedFilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = models.BatchAuditGroup
        formhelper_class = BatchAuditGroupFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class RowDataFilter(HelpedFilterSet):
    # audit_groups = django_filters.ChoiceFilter(lookup_expr="models")

    class Meta:
        model = RowData
        formhelper_class = RowDataFilterFormHelper
        fields = discover_fields(formhelper_class.layout)
