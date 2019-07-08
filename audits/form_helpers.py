from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div

from cases.form_helpers import CollapsibleFilterFormLayout


class FileImporterBatchFilterFormHelper(FormHelper):
    layout = CollapsibleFilterFormLayout(
        Div(
            Div("id", css_class="col"),
            Div("created_on", css_class="col"),
            Div("status", css_class="col"),
            css_class="row",
        )
    )


class FileImporterFilterFormHelper(FormHelper):
    layout = CollapsibleFilterFormLayout(
        Div(
            Div("id", css_class="col"),
            Div("file_path", css_class="col"),
            Div("modified_on", css_class="col"),
            Div("status", css_class="col"),
            Div("acknowledged", css_class="col"),
            css_class="row",
        )
    )


class FileImportAttemptFilterFormHelper(FormHelper):
    layout = CollapsibleFilterFormLayout(
        Div(
            Div("id", css_class="col"),
            Div("imported_from", css_class="col"),
            Div("created_on", css_class="col"),
            Div("status", css_class="col"),
            Div("acknowledged", css_class="col"),
            css_class="row",
        )
    )


class RowDataFilterFormHelper(FormHelper):
    layout = CollapsibleFilterFormLayout(
        Div(
            Div("id", css_class="col"),
            Div("row_num", css_class="col"),
            Div("status", css_class="col"),
            css_class="row",
        )
    )


class ModelImporterFilterFormHelper(FormHelper):
    layout = CollapsibleFilterFormLayout(
        Div(
            Div("id", css_class="col"),
            Div("modified_on", css_class="col"),
            Div("status", css_class="col"),
            Div("row_data", css_class="col"),
            css_class="row",
        )
    )


class ModelImportAttemptFilterFormHelper(FormHelper):
    layout = CollapsibleFilterFormLayout(
        Div(
            Div("id", css_class="col"),
            Div("created_on", css_class="col"),
            Div("content_type", css_class="col"),
            Div("status", css_class="col"),
            css_class="row",
        )
    )
