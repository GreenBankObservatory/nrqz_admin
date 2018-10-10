from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from .models import Attachment, Submission, Facility
from .filters import FacilityFilter, SubmissionFilter
from .tables import FacilityTable, SubmissionTable


class FilterTableView(SingleTableMixin, FilterView):
    table_class = None
    filterset_class = None

    def get_context_data(self, **kwargs):
        if not self.object_list:
            # Need this here to avoid a blank table appearing on first load
            self.object_list = self.table_class.Meta.model.objects.all()
        return super().get_context_data(**kwargs)

class SubmissionListView(FilterTableView):
    table_class = SubmissionTable
    filterset_class = SubmissionFilter
    template_name = "submission/submission_list.html"

class FacilityListView(FilterTableView):
    table_class = FacilityTable
    filterset_class = FacilityFilter
    template_name = "submission/facility_list.html"

class SubmissionDetailView(DetailView):
    model = Submission

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
