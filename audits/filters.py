import django_filters

from cases.filters import HelpedFilterSet
from utils.layout import discover_fields

from . import models
from .form_helpers import BatchAuditFilterFormHelper, BatchAuditGroupFilterFormHelper


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
