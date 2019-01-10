import django_filters

from django_import_data.models import (
    GenericAudit,
    GenericAuditGroup,
    GenericAuditGroupBatch,
    GenericBatchImport,
    RowData,
)

from cases.filters import HelpedFilterSet
from utils.layout import discover_fields


from .form_helpers import (
    GenericAuditFormHelper,
    GenericAuditGroupBatchFormHelper,
    GenericAuditGroupFormHelper,
    GenericBatchImportFormHelper,
    RowDataFilterFormHelper,
)


class GenericAuditFilter(HelpedFilterSet):
    class Meta:
        model = GenericAudit
        formhelper_class = GenericAuditFormHelper
        fields = discover_fields(formhelper_class.layout)


class GenericAuditGroupBatchFilter(HelpedFilterSet):
    class Meta:
        model = GenericAuditGroupBatch
        formhelper_class = GenericAuditGroupBatchFormHelper
        fields = discover_fields(formhelper_class.layout)


class GenericAuditGroupFilter(HelpedFilterSet):
    class Meta:
        model = GenericAuditGroup
        formhelper_class = GenericAuditGroupFormHelper
        fields = discover_fields(formhelper_class.layout)


class GenericBatchImportFilter(HelpedFilterSet):
    class Meta:
        model = GenericBatchImport
        formhelper_class = GenericBatchImportFormHelper
        fields = discover_fields(formhelper_class.layout)


class RowDataFilter(HelpedFilterSet):
    # audit_groups = django_filters.ChoiceFilter(lookup_expr="models")

    class Meta:
        model = RowData
        formhelper_class = RowDataFilterFormHelper
        fields = discover_fields(formhelper_class.layout)
