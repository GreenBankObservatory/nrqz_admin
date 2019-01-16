from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.views.generic.detail import DetailView
from django.views.generic import CreateView
from django.views.generic.base import RedirectView
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

from django_import_data.views import CreateFromImportAttemptView
from django_import_data.models import FileImporter, FileImportAttempt


from cases.views import FilterTableView


from .filters import (
    FileImporterFilter,
    FileImportAttemptFilter,
    ModelImportAttemptFilter,
)
from .tables import FileImporterTable, FileImportAttemptTable, ModelImportAttemptTable

from cases.models import Person, PreliminaryCase, Case, Facility, PreliminaryFacility
from cases.forms import (
    PersonForm,
    PreliminaryCaseForm,
    CaseForm,
    FacilityForm,
    PreliminaryFacilityForm,
)


class PersonCreateFromAuditView(CreateFromImportAttemptView):
    model = Person
    form_class = PersonForm
    template_name = "cases/generic_form.html"


class CaseCreateFromAuditView(CreateFromImportAttemptView):
    model = Case
    form_class = CaseForm
    template_name = "cases/generic_form.html"


class PCaseCreateFromAuditView(CreateFromImportAttemptView):
    model = PreliminaryCase
    form_class = PreliminaryCaseForm
    template_name = "cases/generic_form.html"


class FacilityCreateFromAuditView(CreateFromImportAttemptView):
    model = Facility
    form_class = FacilityForm
    template_name = "cases/generic_form.html"


class PFacilityCreateFromAuditView(CreateFromImportAttemptView):
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


class FileImporterListView(FilterTableView):
    table_class = FileImporterTable
    filterset_class = FileImporterFilter
    template_name = "audits/generic_table.html"


class FileImportAttemptListView(FilterTableView):
    table_class = FileImportAttemptTable
    filterset_class = FileImportAttemptFilter
    template_name = "audits/generic_table.html"


class FileImporterDetailView(DetailView):
    model = FileImporter
    template_name = "audits/fileimporter_detail.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fia_filter = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if not self.fia_filter:
            self.fia_filter = FileImportAttemptFilter(
                self.request.GET,
                queryset=self.object.import_attempts.all(),
                # form_helper_kwargs={"form_class": "collapse"},
            )
            context["fia_filter"] = self.fia_filter

        if "fia_table" not in context:
            table = FileImportAttemptTable(data=self.fia_filter.qs)
            table.paginate(page=self.request.GET.get("page", 1), per_page=10)
            context["fia_table"] = table

        return context


class ModelImportAttemptListView(FilterTableView):
    table_class = ModelImportAttemptTable
    filterset_class = ModelImportAttemptFilter
    template_name = "audits/generic_table.html"


class FileImportAttemptDetailView(DetailView):
    model = FileImportAttempt
    template_name = "audits/fileimportattempt_detail.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mia_filter = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if not self.mia_filter:
            self.mia_filter = ModelImportAttemptFilter(
                self.request.GET,
                queryset=self.object.model_import_attempts.all(),
                # form_helper_kwargs={"form_class": "collapse"},
            )
            context["mia_filter"] = self.mia_filter

        if "mia_table" not in context:
            table = ModelImportAttemptTable(data=self.mia_filter.qs)
            table.paginate(page=self.request.GET.get("page", 1), per_page=10)
            context["mia_table"] = table

        return context
