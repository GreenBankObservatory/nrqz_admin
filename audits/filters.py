import django_filters

from cases.filters import HelpedFilterSet
from utils.layout import discover_fields

from . import models
from .form_helpers import BatchAuditFilterFormHelper


class BatchAuditFilter(HelpedFilterSet):
    class Meta:
        model = models.BatchAudit
        formhelper_class = BatchAuditFilterFormHelper
        fields = discover_fields(formhelper_class.layout)
