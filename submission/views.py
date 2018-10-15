from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.http import HttpResponse

from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from .models import Attachment, Batch, Submission, Facility
from .filters import BatchFilter, FacilityFilter, SubmissionFilter
from .tables import BatchTable, FacilityTable, SubmissionTable
from .kml import (
    facility_as_kml,
    facilities_as_kml,
    submission_as_kml,
    submissions_as_kml,
    kml_to_string,
)


class FilterTableView(SingleTableMixin, FilterView):
    table_class = None
    filterset_class = None

    def get_context_data(self, **kwargs):
        # If there are no query params, then no results are
        # displayed -- but that's not what we want!
        if not self.request.GET:
            # Need this here to avoid a blank table appearing on first load
            self.object_list = self.table_class.Meta.model.objects.all()

        return super().get_context_data(**kwargs)


class BatchListView(FilterTableView):
    table_class = BatchTable
    filterset_class = BatchFilter
    template_name = "submission/batch_list.html"


class BatchDetailView(DetailView):
    model = Batch

    def __init__(self, *args, **kwargs):
        super(BatchDetailView, self).__init__(*args, **kwargs)
        self.submission_filter = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.submission_filter is None:
            self.submission_filter = SubmissionFilter(
                self.request.GET, queryset=self.object.submissions.all()
            )
            context["submission_filter"] = self.submission_filter

        if "submission_table" not in context:
            table = SubmissionTable(data=self.submission_filter.qs)
            table.paginate(page=self.request.GET.get("page", 1), per_page=10)
            context["submission_table"] = table

        return context


class SubmissionListView(FilterTableView):
    table_class = SubmissionTable
    filterset_class = SubmissionFilter
    template_name = "submission/submission_list.html"

    def get(self, request, *args, **kwargs):
        if "kml" in request.GET:
            # TODO: Must be a cleaner way to do this
            qs = self.get_filterset(self.filterset_class).qs
            response = HttpResponse(
                kml_to_string(submissions_as_kml(qs)),
                content_type="application/vnd.google-earth.kml+xml.",
            )
            response["Content-Disposition"] = 'application; filename="nrqz_apps.kml"'
            return response
        else:
            return super(SubmissionListView, self).get(request, *args, **kwargs)


class FacilityListView(FilterTableView):
    table_class = FacilityTable
    filterset_class = FacilityFilter
    template_name = "submission/facility_list.html"

    def get(self, request, *args, **kwargs):
        if "kml" in request.GET:
            # TODO: Must be a cleaner way to do this
            qs = self.get_filterset(self.filterset_class).qs
            response = HttpResponse(
                kml_to_string(facilities_as_kml(qs)),
                content_type="application/vnd.google-earth.kml+xml.",
            )
            response[
                "Content-Disposition"
            ] = 'application; filename="nrqz_facilities.kml"'
            return response
        else:
            return super(FacilityListView, self).get(request, *args, **kwargs)


class SubmissionDetailView(DetailView):
    model = Submission

    def __init__(self, *args, **kwargs):
        super(SubmissionDetailView, self).__init__(*args, **kwargs)
        self.facility_filter = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.facility_filter is None:
            self.facility_filter = FacilityFilter(
                self.request.GET, queryset=self.object.facilities.all()
            )
            context["facility_filter"] = self.facility_filter

        if "facility_table" not in context:
            table = FacilityTable(data=self.facility_filter.qs)
            table.paginate(page=self.request.GET.get("page", 1), per_page=10)
            context["facility_table"] = table

        return context

    def as_kml(self):
        submission_as_kml(self.object)


class FacilityDetailView(DetailView):
    model = Facility

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meta_info"] = ["id", "created_on", "modified_on"]

        context["location_info"] = ["latitude", "longitude", "amsl", "agl"]
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

        context["other_info"] = ["site_name", "call_sign", "fcc_file_number"]

        return context

    def as_kml(self):
        facility_as_kml(self.object)


class AttachmentListView(ListView):
    model = Attachment


class AttachmentDetailView(DetailView):
    model = Attachment
