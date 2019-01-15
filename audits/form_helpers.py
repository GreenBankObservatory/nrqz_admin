from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div

from cases.form_helpers import CollapsibleFilterFormLayout


class ModelImportAttemptFilterFormHelper(FormHelper):
    layout = CollapsibleFilterFormLayout(
        Div(
            Div("id", css_class="col"),
            # Div("audit_group", css_class="col"),
            Div("status", css_class="col"),
            css_class="row",
        )
    )


class FileImportAttemptFilterFormHelper(FormHelper):
    layout = CollapsibleFilterFormLayout(
        Div(
            Div("imported_from", css_class="col"),
            Div("status", css_class="col"),
            Div("created_on", css_class="col"),
            css_class="row",
        )
    )


class FileImporterFilterFormHelper(FormHelper):
    layout = CollapsibleFilterFormLayout(
        Div(
            Div("last_imported_path", css_class="col"),
            # Div("fil", css_class="col"),
            Div("status", css_class="col"),
            css_class="row",
        )
    )


class RowDataFilterFormHelper(FormHelper):
    layout = CollapsibleFilterFormLayout(
        Div(
            Div("id", css_class="col"),
            # Div("genericauditgroup_audit_groups__status", css_class="col"),
            css_class="row",
        )
    )
