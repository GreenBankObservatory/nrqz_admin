from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.views.generic.detail import DetailView
from django.views.generic import CreateView
from django.views.generic.base import RedirectView
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

from django_import_data.views import CreateFromAuditView


from cases.views import FilterTableView
from .models import BatchAudit, BatchAuditGroup
from .filters import BatchAuditFilter, BatchAuditGroupFilter, RowDataFilter
from .tables import BatchAuditTable, BatchAuditGroupTable, RowDataTable

from cases.models import Person, PreliminaryCase, Case, Facility, PreliminaryFacility
from cases.forms import (
    PersonForm,
    PreliminaryCaseForm,
    CaseForm,
    FacilityForm,
    PreliminaryFacilityForm,
)

# from importers.excel.excel_importer import ExcelImporter


class BatchAuditGroupListView(FilterTableView):
    table_class = BatchAuditGroupTable
    filterset_class = BatchAuditGroupFilter
    template_name = "audits/batch_audit_group_list.html"


class BatchAuditGroupDetailView(DetailView):
    model = BatchAuditGroup


class BatchAuditListView(FilterTableView):
    table_class = BatchAuditTable
    filterset_class = BatchAuditFilter
    template_name = "audits/batch_audit_list.html"


class BatchAuditDetailView(DetailView):
    model = BatchAudit


class BatchAuditCreateView(CreateView):
    model = BatchAudit
    fields = ["audit_group", "original_file"]
    # template_name = "audits/batchaudit_form.html"

    # def __init__(self, *args, **kwargs):
    #     import ipdb

    #     ipdb.set_trace()
    #     super().__init__(*args, **kwargs)

    # def get(self, request, *args, **kwargs):
    #     batch_audit = self.get_object()
    #     return HttpResponseRedirect(reverse("batch_audit", args=[str(batch_audit.id)]))

    def post(self, request, *args, **kwargs):
        bag_id = request.POST.get("audit_group", None)
        path = request.POST.get("original_file", None)
        print("PATH", path)
        bag = get_object_or_404(BatchAuditGroup, id=bag_id)
        ec = ExcelImporter(path=path, durable=True, batch_audit_group=bag)
        try:
            batch_audit = ec.process()
        except FileNotFoundError as error:
            messages.error(request, f"Failed to create BatchAudit: {error}")
            batch_audit = None
        else:
            messages.success(
                request,
                f"Successfully created BatchAudit {batch_audit} <{batch_audit.id}>",
            )
            if batch_audit.status == "created_clean":
                messages.success(
                    request,
                    f"Successfully imported Batch {batch_audit.audit_group.batch.id}",
                )
            elif batch_audit.status == "created_dirty":
                messages.warning(
                    request,
                    f"Successfully imported Batch {batch_audit.audit_group.batch.id} (with some minor errors)",
                )
            elif batch_audit.status == "rejected":
                messages.error(
                    request, f"Failed to import Batch from {batch_audit.original_file}"
                )
            else:
                # TODO: FIX this
                raise ValueError("Something has gone terribly wrong")

        if batch_audit:
            return HttpResponseRedirect(
                reverse("batch_audit_detail", args=[str(batch_audit.id)])
            )
        # TODO: Fix this!
        return HttpResponseRedirect(reverse("batch_audit_list"))


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
