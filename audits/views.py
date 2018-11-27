from django.shortcuts import render
from django.views.generic.detail import DetailView

from cases.views import FilterTableView
from .models import BatchAudit
from .filters import BatchAuditFilter
from .tables import BatchAuditTable
from utils.numrange import get_str_from_nums


class BatchAuditListView(FilterTableView):
    table_class = BatchAuditTable
    filterset_class = BatchAuditFilter
    template_name = "audits/batch_audit_list.html"


class BatchAuditDetailView(DetailView):
    model = BatchAudit

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)

    #     context["Err"]

    #     return context
