from django.views.generic.detail import DetailView

from submission.views import FilterTableView

from .models import Applicant
from .tables import ApplicantTable
from .filters import ApplicantFilter


class ApplicantListView(FilterTableView):
    table_class = ApplicantTable
    filterset_class = ApplicantFilter
    template_name = "applicants/applicant_list.html"


class ApplicantDetailView(DetailView):
    model = Applicant

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["applicant_info"] = [
            "nrqz_no",
            "applicant",
            "contact",
            "phone",
            "fax",
            "email",
            "street",
            "city",
            "county",
            "state",
            "zipcode",
        ]

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

        context["attachment_info"] = [
            "letter1",
            "letter2",
            "letter3",
            "letter4",
            "letter5",
            "letter6",
            "letter7",
            "letter8",
        ]
        return context
