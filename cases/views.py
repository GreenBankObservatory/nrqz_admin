from django.views.generic.detail import DetailView
from django.http import HttpResponse

from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from .models import Attachment, Batch, Case, Facility, Person
from .filters import (
    AttachmentFilter,
    BatchFilter,
    FacilityFilter,
    PersonFilter,
    CaseFilter,
)
from .tables import (
    AttachmentTable,
    BatchTable,
    FacilityTable,
    PersonTable,
    CaseTable,
)

from .kml import (
    facility_as_kml,
    facilities_as_kml,
    case_as_kml,
    cases_as_kml,
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
    template_name = "cases/batch_list.html"


class BatchDetailView(DetailView):
    model = Batch

    def __init__(self, *args, **kwargs):
        super(BatchDetailView, self).__init__(*args, **kwargs)
        self.case_filter = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.case_filter is None:
            self.case_filter = CaseFilter(
                self.request.GET, queryset=self.object.cases.all()
            )
            context["case_filter"] = self.case_filter

        if "case_table" not in context:
            table = CaseTable(data=self.case_filter.qs)
            table.paginate(page=self.request.GET.get("page", 1), per_page=10)
            context["case_table"] = table

        return context


class CaseListView(FilterTableView):
    table_class = CaseTable
    filterset_class = CaseFilter
    template_name = "cases/case_list.html"

    def get(self, request, *args, **kwargs):
        if "kml" in request.GET:
            # TODO: Must be a cleaner way to do this
            qs = self.get_filterset(self.filterset_class).qs
            response = HttpResponse(
                kml_to_string(cases_as_kml(qs)),
                content_type="application/vnd.google-earth.kml+xml.",
            )
            response["Content-Disposition"] = 'application; filename="nrqz_apps.kml"'
            return response
        else:
            return super(CaseListView, self).get(request, *args, **kwargs)


class FacilityListView(FilterTableView):
    table_class = FacilityTable
    filterset_class = FacilityFilter
    template_name = "cases/facility_list.html"

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


class CaseDetailView(DetailView):
    model = Case

    def __init__(self, *args, **kwargs):
        super(CaseDetailView, self).__init__(*args, **kwargs)
        self.facility_filter = None
        self.attachment_filter = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["status_info"] = [
            "completed",
            "shutdown",
            "completed_on",
            "sgrs_notify",
            "sgrs_notified_on",
            "si_waived",
            "si",
            "si_done",
        ]

        context["application_info"] = [
            "radio_service",
            "call_sign",
            "fcc_freq_coord",
            "fcc_file_num",
            "num_freqs",
            "num_sites",
            "num_outside",
            "erpd_limit",
        ]

        if not self.facility_filter:
            self.facility_filter = FacilityFilter(
                self.request.GET, queryset=self.object.facilities.all()
            )
            context["facility_filter"] = self.facility_filter

        if "facility_table" not in context:
            table = FacilityTable(data=self.facility_filter.qs)
            table.paginate(page=self.request.GET.get("page", 1), per_page=10)
            context["facility_table"] = table


        if not self.attachment_filter:
            self.attachment_filter = AttachmentFilter(
                self.request.GET, queryset=self.object.attachments.all()
            )
            context["attachment_filter"] = self.attachment_filter

        if "attachment_table" not in context:
            table = AttachmentTable(data=self.attachment_filter.qs)
            table.paginate(page=self.request.GET.get("page", 1), per_page=10)
            context["attachment_table"] = table

        return context

    def as_kml(self):
        case_as_kml(self.object)


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


class AttachmentListView(FilterTableView):
    table_class = AttachmentTable
    filterset_class = AttachmentFilter
    template_name = "cases/attachment_list.html"


class AttachmentDetailView(DetailView):
    model = Attachment

    def __init__(self, *args, **kwargs):
        super(AttachmentDetailView, self).__init__(*args, **kwargs)
        self.case_filter = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meta_info"] = ["id", "created_on", "modified_on"]

        if self.case_filter is None:
            self.case_filter = CaseFilter(
                self.request.GET, queryset=self.object.cases.all()
            )
            context["case_filter"] = self.case_filter

        if "case_table" not in context:
            table = CaseTable(data=self.case_filter.qs)
            table.paginate(page=self.request.GET.get("page", 1), per_page=10)
            context["case_table"] = table

        return context


class PersonListView(FilterTableView):
    table_class = PersonTable
    filterset_class = PersonFilter
    template_name = "cases/person_list.html"


class PersonDetailView(DetailView):
    model = Person

    def __init__(self, *args, **kwargs):
        super(PersonDetailView, self).__init__(*args, **kwargs)
        self.case_filter = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["applicant_info"] = [
            # "cases",
            "name",
            "phone",
            "fax",
            "email",
            "street",
            "city",
            "county",
            "state",
            "zipcode",
        ]

        if self.case_filter is None:
            self.case_filter = CaseFilter(
                self.request.GET, queryset=self.object.applicant_for_cases.all()
            )
            context["case_filter"] = self.case_filter

        if "case_table" not in context:
            table = CaseTable(data=self.case_filter.qs)
            table.paginate(page=self.request.GET.get("page", 1), per_page=10)
            context["case_table"] = table

        return context
