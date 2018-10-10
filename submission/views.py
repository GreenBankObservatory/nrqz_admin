from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.db.models.aggregates import Max
from crispy_forms.layout import Submit, Layout, ButtonHolder, Div
from crispy_forms.helper import FormHelper

from .filters import FacilityFilter, SubmissionFilter
from .tables import FacilityTable, SubmissionTable

from .models import Attachment, Submission, Facility

def submission_list(request):
    filter_ = SubmissionFilter(request.GET, queryset=Submission.objects.all())
    filter_.form.helper = FormHelper()
    filter_.form.helper.form_method = "get"
    filter_.form.helper.layout = Layout(
        Div(
            Div("created_on", css_class="col"),
            Div("name", css_class="col"),
            Div("comments", css_class="col"),
            css_class="row",
        ),
        ButtonHolder(Submit("submit", "Filter")),
    )

    # Can't get this to work with CBV, so I hacked this together
    # Use the filter's queryset, but with ONLY the fields specified in the filter
    # This is to prevent the table from coming up as blank initially
    table = SubmissionTable(data=filter_.qs)
    table.paginate(page=request.GET.get("page", 1), per_page=25)
    return render(
        request, "submission/submission_list.html", {"filter": filter_, "table": table}
    )

class SubmissionDetailView(DetailView):
    model = Submission


def facility_list(request):
    filter_ = FacilityFilter(request.GET, queryset=Facility.objects.all())
    filter_.form.helper = FormHelper()
    filter_.form.helper.form_method = "get"
    filter_.form.helper.layout = Layout(
        Div(
            Div("site_name", "nrqz_id", css_class="col"),
            Div("latitude", "longitude", css_class="col"),
            Div("amsl", "agl", css_class="col"),
            Div("freq_low", "freq_high", css_class="col"),
            css_class="row",
        ),
        ButtonHolder(Submit("submit", "Filter")),
    )

    # Can't get this to work with CBV, so I hacked this together
    # Use the filter's queryset, but with ONLY the fields specified in the filter
    # This is to prevent the table from coming up as blank initially
    table = FacilityTable(data=filter_.qs.only(*FacilityFilter.Meta.fields))
    table.paginate(page=request.GET.get("page", 1), per_page=25)
    return render(
        request, "submission/facility_list.html", {"filter": filter_, "table": table}
    )


class FacilityDetailView(DetailView):
    model = Facility

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meta_info"] = ["id", "created_on", "modified_on"]

        context["location_info"] = [
            "latitude",
            "longitude",
            "amsl",
            "agl",
        ]
        context["antenna_info"] = [
            "freq_low",
            "freq_high",
            "bandwidth",
            "max_output",
            "antenna_gain",
            "system_loss",
            "main_beam_orientation",
            "mechanical_downtilt",
            "electrical_downtilt",
            "antenna_model_number",
        ]

        context["cell_info"] = [
            "tx_per_sector",
            "tx_antennas_per_sector",
            "technology",
            "uses_split_sectorization",
            "uses_cross_polarization",
            "num_quad_or_octal_ports_with_feed_power",
            "tx_power_pos_45",
            "tx_power_neg_45",
        ]

        context["other_info"] = [
            "site_name",
            "call_sign",
            "fcc_file_number",
        ]

        return context


class AttachmentListView(ListView):
    model = Attachment


class AttachmentDetailView(DetailView):
    model = Attachment
