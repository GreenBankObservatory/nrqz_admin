"""Custom crispy_forms.helper.FormHelper sub-classes for cases app"""

from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Submit, Layout, Div, Reset


class CollapsibleFilterFormLayout(Layout):
    def __init__(self, *args):
        super(CollapsibleFilterFormLayout, self).__init__(
            Div(
                *args,
                FormActions(
                    Submit("submit", "Filter"),
                    Reset("reset", "Reset"),
                    Submit(
                        "kml",
                        "As .kml",
                        title=(
                            "Download the locations of all currently-filtered "
                            "Facilities as a .kml file"
                        ),
                    ),
                    css_class="filter-form-buttons",
                ),
                css_class="container-fluid filter-form",
            )
        )


class LetterFormHelper(FormHelper):
    layout = Layout(
        Div(
            Div(Field("cases", css_class="no-form-control"), css_class="col"),
            Div(Field("facilities", css_class="no-form-control"), css_class="col"),
            Div("template", css_class="col"),
            css_class="row",
        ),
        FormActions(
            Submit(
                "submit",
                "Render",
                title="Re-render the template with the above choices",
            ),
            Submit("download", "Download", title="Download as .docx"),
            css_class="float-right filter-form-buttons",
        ),
    )


class BatchFilterFormHelper(FormHelper):
    """Provides layout information for FacilityFilter.form"""

    layout = CollapsibleFilterFormLayout(
        Div(
            Div("name", css_class="col"),
            Div("comments", css_class="col"),
            css_class="row",
        )
    )


class FacilityFilterFormHelper(FormHelper):
    """Provides layout information for FacilityFilter.form"""

    layout = CollapsibleFilterFormLayout(
        Div(
            Div("nrqz_id", "site_name", css_class="col-sm-2"),
            Div("freq_high", "freq_low", css_class="col-sm-5"),
            Div("structure", "comments", css_class="col-sm-5"),
            Div("location", css_class="col-sm-12"),
            css_class="row",
        )
    )


class CaseFilterFormHelper(FormHelper):
    """Provides layout information for CaseFilter.form"""

    layout = CollapsibleFilterFormLayout(
        Div(
            Div("case_num", "applicant", "contact", css_class="col"),
            Div("radio_service", "call_sign", "fcc_file_num", css_class="col"),
            Div("completed", "shutdown", "comments", css_class="col"),
            css_class="row",
        )
    )


class PersonFilterFormHelper(FormHelper):
    """Provides layout information for PersonFilter.form"""

    layout = Layout(
        Div(
            Div("name", "email", "phone", css_class="col"),
            Div("street", "city", "state", "zipcode", "comments", css_class="col"),
            css_class="row",
        ),
        FormActions(Submit("submit", "Filter")),
    )


class AttachmentFilterFormHelper(FormHelper):
    """Provides layout information for AttachmentFilter.form"""

    layout = Layout(
        Div(
            Div("path", css_class="col"),
            Div("comments", css_class="col"),
            css_class="row",
        ),
        FormActions(Submit("submit", "Filter")),
    )


class StructureFilterFormHelper(FormHelper):
    """Provides layout information for StructureFilter.form"""

    layout = CollapsibleFilterFormLayout(
        Div(
            Div("asr", "file_num", css_class="col"),
            Div("height", "faa_circ_num", css_class="col"),
            Div("faa_study_num", "issue_date", css_class="col"),
            Div("location", css_class="col-sm-12"),
            css_class="row",
        )
    )
