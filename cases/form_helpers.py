"""Custom crispy_forms.helper.FormHelper sub-classes for cases app"""

from crispy_forms.bootstrap import FormActions, InlineField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Reset, Submit


class CollapsibleFilterFormLayout(Layout):
    def __init__(self, *args, extra_buttons=None):
        if extra_buttons is None:
            extra_buttons = []
        super(CollapsibleFilterFormLayout, self).__init__(
            Div(
                *args,
                FormActions(
                    Submit("submit", "Filter"),
                    Submit("clear", "Clear"),
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
                "power_density_limit",
                css_class="col",
            ),
            Div(
                "location",
                "comments",
                "distance_to_gbt",
                "azimuth_to_gbt",
                "in_nrqz",
                css_class="col",
            ),
            css_class="row",
        ),
        extra_buttons=[
            Submit(
                "_export",
                "Export as .csv",
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
                "bandwidth",
                "distance_to_gbt",
                css_class="col-sm-5",
            ),
            Div(
                "azimuth_to_gbt",
                "nrao_aerpd",
                "requested_max_erp_per_tx",
                "data_source",
                "search",
                css_class="col-sm-5",
            ),
            css_class="row",
        ),
        Div(
            Div("si_done", css_class="col-sm-5"),
            Div("location", css_class="col-sm-7"),
            css_class="row",
        ),
        extra_buttons=[
            Submit(
                "kml",
                "Export as .kml",
                title=(
                    "Download the locations of all currently-filtered "
                    "Facilities as a .kml file"
                ),
            ),
            Submit(
                "_export",
                "Export as .csv",
                title=(
                    "Download the locations of all currently-filtered "
                    "Facilities as a .csv file"
                ),
            ),
        ],
    )


class CaseGroupFilterFormHelper(FormHelper):
    """Provides layout information for CaseGroupFilter.form"""

    layout = CollapsibleFilterFormLayout(
        Div(
            Div("id", css_class="col"),
            Div("comments", css_class="col"),
            Div("num_cases", css_class="col"),
            Div("num_pcases", css_class="col"),
            Div("completed", css_class="col"),
            css_class="row",
        )
    )


class PreliminaryCaseFilterFormHelper(FormHelper):
    """Provides layout information for PreliminaryCaseFilter.form"""

    layout = CollapsibleFilterFormLayout(
        Div(
            Div("case_num", "applicant", "contact", css_class="col"),
            Div("radio_service", "completed", "is_federal", css_class="col"),
            css_class="row",
        ),
        extra_buttons=[
            Submit(
                "_export",
                "Export as .csv",
                title=(
                    "Download the locations of all currently-filtered "
                    "PCases as a .csv file"
                ),
            )
        ],
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
            Div("date_recorded", "completed", "is_federal", "search", css_class="col"),
            css_class="row",
        ),
        Div(
            Div("num_sites", css_class="col"),
            Div("num_facilities", css_class="col"),
            Div("si_done", css_class="col"),
            css_class="row",
        ),
        extra_buttons=[
            Submit(
                "kml",
                "Export as .kml",
                title=(
                    "Download the locations of all currently-filtered "
                    "Facilities as a .kml file"
                ),
            ),
            Submit(
                "_export",
                "Export as .csv",
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
                "Export as .csv",
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
        Div(
            Div("file_path", css_class="col"),
            Div("comments", css_class="col"),
            Div("original_index", css_class="col"),
            Div("data_source", css_class="col"),
            Div("hash_on_disk", css_class="col"),
            Div("is_active", css_class="col"),
            css_class="row",
        )
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
                "Export as .csv",
                title=(
                    "Download the locations of all currently-filtered "
                    "Facilities as a .csv file"
                ),
            )
        ],
    )


# class DuplicateCaseFormHelper(FormHelper):
#     form_method = "post"
#     form_action = reverse("duplicate_case", args=)
#     layout = Div("num_duplicates", Submit("submit", "Filter"),


class CaseFormHelper(FormHelper):
    form_class = "readable-form mx-auto"

    layout = Layout(
        Div(
            Div(
                Div(InlineField("case_num"), css_class="col"),
                Div(InlineField("radio_service"), css_class="col"),
                Div(InlineField("call_sign"), css_class="col"),
                Div(InlineField("is_federal"), css_class="col"),
                css_class="row",
            ),
            Div(
                Div(InlineField("date_recorded"), css_class="col"),
                Div(InlineField("completed_on"), css_class="col"),
                css_class="row",
            ),
            Div(
                Div(InlineField("agency_num"), css_class="col"),
                Div(InlineField("applicant"), css_class="col"),
                Div(InlineField("contact"), css_class="col"),
                css_class="row",
            ),
            Div(
                Div(InlineField("freq_coord"), css_class="col"),
                Div(InlineField("fcc_file_num"), css_class="col"),
                css_class="row",
            ),
            Div(
                Div(InlineField("sgrs_notify"), css_class="col"),
                Div(InlineField("sgrs_responded_on"), css_class="col"),
                Div(InlineField("sgrs_service_num"), css_class="col"),
                css_class="row",
            ),
            Div(
                Div(InlineField("shutdown"), css_class="col"),
                Div(InlineField("si"), css_class="col"),
                # Div(InlineField("si_done"), css_class="col"),
                Div(InlineField("si_waived"), css_class="col"),
                css_class="row",
            ),
            Div(
                Div(InlineField("num_freqs"), css_class="col"),
                Div(InlineField("num_sites"), css_class="col"),
                Div(InlineField("num_outside"), css_class="col"),
                css_class="row",
            ),
            Div(Div(InlineField("comments"), css_class="col"), css_class="row"),
            Div(Div(InlineField("attachments"), css_class="col"), css_class="row"),
            css_class="",
        ),
        # Submit("submit", "Submit"),
    )


class PersonFormHelper(FormHelper):
    form_class = "readable-form mx-auto"

    layout = Layout(
        Div(
            Div(
                Div(InlineField("name"), css_class="col"),
                Div(InlineField("email"), css_class="col"),
                Div(InlineField("phone"), css_class="col"),
                Div(InlineField("fax"), css_class="col"),
                css_class="row",
            ),
            Div(
                Div(InlineField("street"), css_class="col"),
                Div(InlineField("city"), css_class="col"),
                Div(InlineField("county"), css_class="col"),
                Div(InlineField("state"), css_class="col"),
                Div(InlineField("zipcode"), css_class="col"),
                css_class="row",
            ),
            Div(Div(InlineField("comments"), css_class="col"), css_class="row"),
        ),
        Submit("submit", "Submit"),
    )
