from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.views.generic.detail import DetailView
from django.views.generic import CreateView
from django.views.generic.base import RedirectView
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

from django_import_data.views import CreateFromAuditView
from django_import_data.models import (
    GenericAuditGroupBatch,
    GenericBatchImport,
    GenericAuditGroup,
)


from cases.views import FilterTableView


from .filters import (
    GenericAuditGroupBatchFilter,
    GenericBatchImportFilter,
    RowDataFilter,
    GenericAuditGroupFilter,
    GenericAuditFilter,
)
from .tables import (
    GenericAuditGroupBatchTable,
    GenericBatchImportTable,
    RowDataTable,
    GenericAuditGroupTable,
    GenericAuditTable,
)

from cases.models import Person, PreliminaryCase, Case, Facility, PreliminaryFacility
from cases.forms import (
    PersonForm,
    PreliminaryCaseForm,
    CaseForm,
    FacilityForm,
    PreliminaryFacilityForm,
)


class PersonCreateFromAuditView(CreateFromAuditView):
    model = Person
    form_class = PersonForm
    template_name = "cases/generic_form.html"


class CaseCreateFromAuditView(CreateFromAuditView):
    model = Case
    form_class = CaseForm
    template_name = "cases/generic_form.html"


class PCaseCreateFromAuditView(CreateFromAuditView):
    model = PreliminaryCase
    form_class = PreliminaryCaseForm
    template_name = "cases/generic_form.html"


class FacilityCreateFromAuditView(CreateFromAuditView):
    model = Facility
    form_class = FacilityForm
    template_name = "cases/generic_form.html"


class PFacilityCreateFromAuditView(CreateFromAuditView):
    model = PreliminaryFacility
    form_class = PreliminaryFacilityForm
    template_name = "cases/generic_form.html"


class CreateFromAuditRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse(
            f"{kwargs['model']}_create_from_audit",
            kwargs={"audit_pk": kwargs.get("audit_pk", None)},
        )
        # return super().get_redirect_url(*args, **kwargs)


class RowDataListView(FilterTableView):
    table_class = RowDataTable
    filterset_class = RowDataFilter
    template_name = "audits/rowdata_list.html"


# class RowDataDetailView(DetailView):
#     model = RowData


class GenericAuditGroupBatchListView(FilterTableView):
    table_class = GenericAuditGroupBatchTable
    filterset_class = GenericAuditGroupBatchFilter
    template_name = "audits/generic_table.html"


class GenericBatchImportListView(FilterTableView):
    table_class = GenericBatchImportTable
    filterset_class = GenericBatchImportFilter
    template_name = "audits/generic_table.html"


class GenericAuditGroupDetailView(DetailView):
    model = GenericAuditGroup
    template_name = "genericauditgroup_detail.html"


class GenericAuditGroupBatchDetailView(DetailView):
    model = GenericAuditGroupBatch
    template_name = "audits/genericauditgroupbatch_detail.html"


class GenericAuditGroupListView(FilterTableView):
    table_class = GenericAuditGroupTable
    filterset_class = GenericAuditGroupFilter
    template_name = "audits/generic_table.html"


class GenericAuditListView(FilterTableView):
    table_class = GenericAuditTable
    filterset_class = GenericAuditFilter
    template_name = "audits/generic_table.html"


class GenericBatchImportDetailView(DetailView):
    model = GenericBatchImport
    template_name = "audits/genericbatchimport_detail.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ag_filter = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if not self.ag_filter:
            self.ag_filter = GenericAuditGroupFilter(
                self.request.GET,
                queryset=self.object.audit_groups.all(),
                # form_helper_kwargs={"form_class": "collapse"},
            )
            context["ag_filter"] = self.ag_filter

        if "ag_table" not in context:
            table = GenericAuditGroupTable(data=self.ag_filter.qs)
            table.paginate(page=self.request.GET.get("page", 1), per_page=10)
            context["ag_table"] = table

        return context
