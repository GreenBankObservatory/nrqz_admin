"""Custom crispy_forms.helper.FormHelper sub-classes for cases app"""

from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Submit, Layout, Div, Reset


class CollapsibleFilterFormLayout(Layout):
    def __init__(self, *args, extra_buttons=None):
        if extra_buttons is None:
            extra_buttons = []
        super(CollapsibleFilterFormLayout, self).__init__(
            Div(
                *args,
                FormActions(
                    Submit("submit", "Filter"),
                    Reset("reset", "Reset"),
                    Submit("show-all", "Show All"),
                    Submit("mass-edit", "Mass Edit"),
                    *extra_buttons,
                    css_class="filter-form-buttons",
                ),
                css_class="container-fluid filter-form",
            )
        )


class LetterFormHelper(FormHelper):
    form_method = "post"

    layout = Layout(
        Div(
            Div(Field("cases", css_class="no-form-control"), css_class="col"),
            Div(Field("facilities", css_class="no-form-control"), css_class="col"),
            Div("template", css_class="col"),
            css_class="row",
        ),
        FormActions(
            Submit("submit", "Download", title="Download as .docx"),
            css_class="float-right filter-form-buttons",
        ),
    )


class PreliminaryFacilityFilterFormHelper(FormHelper):
    """Provides layout information for PreliminaryFacilityFilter.form"""

    layout = CollapsibleFilterFormLayout(
        Div(
            Div(
                "nrqz_id",
                "pcase",
                "site_num",
                "location_description",
                "freq_low",
                css_class="col",
            ),
            Div("power_density_limit", "location", "comments", css_class="col"),
            Div("distance_to_gbt", "azimuth_to_gbt", "in_nrqz", css_class="col"),
            css_class="row",
        ),
        extra_buttons=[
            Submit(
                "_export",
                "csv",
                title=(
                    "Download the locations of all currently-filtered "
                    "PFacilities as a .csv file"
                ),
            )
        ],
    )


class FacilityFilterFormHelper(FormHelper):
    """Provides layout information for FacilityFilter.form"""

    layout = CollapsibleFilterFormLayout(
        Div(
            Div(
                "nrqz_id",
                "case",
                "site_name",
                "applicant",
                "contact",
                css_class="col-sm-2",
            ),
            Div(
                "main_beam_orientation",
                "freq_low",
                "freq_high",
                "distance_to_gbt",
                "azimuth_to_gbt",
                css_class="col-sm-5",
            ),
            Div(
                "nrao_aerpd",
                "requested_max_erp_per_tx",
                "data_source",
                "comments",
                "search",
                css_class="col-sm-5",
            ),
            css_class="row",
        ),
        Div(Div("location", css_class="col-sm-7"), css_class="row"),
        extra_buttons=[
            Submit(
                "kml",
                "As .kml",
                title=(
                    "Download the locations of all currently-filtered "
                    "Facilities as a .kml file"
                ),
            ),
            Submit(
                "_export",
                "csv",
                title=(
                    "Download the locations of all currently-filtered "
                    "Facilities as a .csv file"
                ),
            ),
        ],
    )


class PreliminaryCaseGroupFilterFormHelper(FormHelper):
    """Provides layout information for PreliminaryCaseGroupFilter.form"""

    layout = CollapsibleFilterFormLayout(
        Div(
            Div("id", css_class="col"),
            Div("comments", css_class="col"),
            css_class="row",
        )
    )


class PreliminaryCaseFilterFormHelper(FormHelper):
    """Provides layout information for PreliminaryCaseFilter.form"""

    layout = CollapsibleFilterFormLayout(
        Div(
            Div("case_num", "applicant", "contact", css_class="col"),
            Div("radio_service", "completed", "comments", css_class="col"),
            Div("is_federal", css_class="col"),
            css_class="row",
        )
    )


class CaseFilterFormHelper(FormHelper):
    """Provides layout information for CaseFilter.form"""

    layout = CollapsibleFilterFormLayout(
        Div(
            Div("case_num", "applicant", "contact", "call_sign", css_class="col"),
            Div(
                "freq_coord",
                "fcc_file_num",
                "meets_erpd_limit",
                "sgrs_approval",
                css_class="col",
            ),
            Div(
                "date_recorded",
                "completed",
                "comments",
                "is_federal",
                "search",
                css_class="col",
            ),
            css_class="row",
        ),
        extra_buttons=[
            Submit(
                "kml",
                "As .kml",
                title=(
                    "Download the locations of all currently-filtered "
                    "Facilities as a .kml file"
                ),
            ),
            Submit(
                "_export",
                "csv",
                title=(
                    "Download the locations of all currently-filtered "
                    "Facilities as a .csv file"
                ),
            ),
        ],
    )


class PersonFilterFormHelper(FormHelper):
    """Provides layout information for PersonFilter.form"""

    layout = CollapsibleFilterFormLayout(
        Div(
            Div("name", "street", css_class="col"),
            Div("email", "city", css_class="col"),
            Div("state", "phone", css_class="col"),
            Div("comments", "zipcode", css_class="col"),
            css_class="row",
        ),
        extra_buttons=[
            Submit(
                "_export",
                "csv",
                title=(
                    "Download the locations of all currently-filtered "
                    "Facilities as a .csv file"
                ),
            )
        ],
    )


class AttachmentFilterFormHelper(FormHelper):
    """Provides layout information for AttachmentFilter.form"""

    layout = CollapsibleFilterFormLayout(
        Div(Div("path", "original_index", css_class="col"), css_class="row")
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
        ),
        extra_buttons=[
            Submit(
                "_export",
                "csv",
                title=(
                    "Download the locations of all currently-filtered "
                    "Facilities as a .csv file"
                ),
            )
        ],
    )
