from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div

from cases.form_helpers import CollapsibleFilterFormLayout


class GenericAuditFormHelper(FormHelper):
    layout = CollapsibleFilterFormLayout(
        Div(
            Div("id", css_class="col"),
            Div("audit_group", css_class="col"),
            Div("status", css_class="col"),
            css_class="row",
        )
    )


class BatchAuditFilterFormHelper(FormHelper):
    layout = CollapsibleFilterFormLayout(
        Div(
            Div("original_file", css_class="col"),
            Div("status", css_class="col"),
            Div("created_on", css_class="col"),
            css_class="row",
        )
    )


class BatchAuditGroupFilterFormHelper(FormHelper):
    layout = CollapsibleFilterFormLayout(
        Div(
            Div("last_imported_path", css_class="col"),
            Div("batch", css_class="col"),
            Div("status", css_class="col"),
            css_class="row",
        )
    )


class RowDataFilterFormHelper(FormHelper):
    layout = CollapsibleFilterFormLayout(
        Div(
            Div("id", css_class="col"),
            Div("genericauditgroup_audit_groups__status", css_class="col"),
            css_class="row",
        )
    )


class GenericAuditGroupBatchFormHelper(FormHelper):
    layout = CollapsibleFilterFormLayout(
        Div(
            Div("id", css_class="col"),
            Div("imports", css_class="col"),
            Div("last_imported_path", css_class="col"),
            Div("status", css_class="col"),
            css_class="row",
        )
    )


class GenericBatchImportFormHelper(FormHelper):
    layout = CollapsibleFilterFormLayout(
        Div(
            Div("id", css_class="col"),
            # Div("audit_groups", css_class="col"),
            Div("status", css_class="col"),
            css_class="row",
        )
    )


class GenericAuditGroupFormHelper(FormHelper):
    layout = CollapsibleFilterFormLayout(
        Div(
            Div("id", css_class="col"),
            Div("importee_class", css_class="col"),
            Div("status", css_class="col"),
            css_class="row",
        )
    )
