from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Submit, Layout, Div, Reset

from cases.form_helpers import CollapsibleFilterFormLayout


class BatchAuditFilterFormHelper(FormHelper):
    layout = CollapsibleFilterFormLayout(
        Div(
            Div("original_file", css_class="col"),
            Div("status", css_class="col"),
            Div("created_on", css_class="col"),
            css_class="row",
        )
    )
