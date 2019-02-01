from django.contrib import messages
from django.core.management import call_command
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView

from django_import_data.views import CreateFromImportAttemptView
from django_import_data.models import FileImporter, FileImportAttempt


from cases.views import FilterTableView

from .filters import (
    FileImporterFilter,
    FileImportAttemptFilter,
    ModelImportAttemptFilter,
)
from .tables import FileImporterTable, FileImportAttemptTable, ModelImportAttemptTable
from .forms import FileImporterForm
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
    template_name = "audits/fileimporter_index.html"


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
                queryset=self.object.file_import_attempts.all(),
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


@transaction.atomic
def _import_file(request, file_importer):
    importer_name = file_importer.importer_name
    path = file_importer.last_imported_path
    try:
        call_command(importer_name, path, overwrite=True, durable=True)
    except Exception as error:
        messages.error(request, f"FATAL ERROR: {error.__class__.__name__}: {error}")
        return HttpResponseRedirect(file_importer.get_absolute_url())

    file_import_attempt = file_importer.most_recent_import
    messages.success(
        request,
        f"Successfully created {file_import_attempt._meta.verbose_name} "
        f"for path {file_import_attempt.name}!",
    )

    STATUSES = file_import_attempt.STATUSES
    status = STATUSES[file_import_attempt.status]
    status_display = file_import_attempt.get_status_display()
    if status == STATUSES.rejected:
        messager = messages.error
        message_stub = (
            "However, one or more Model Import Attempts failed (no model was created)!"
        )
    elif status == STATUSES.created_dirty:
        messager = messages.warning
        message_stub = (
            "All Model Import Attempts were successful, however, "
            "one or more Model Import Attempts were created with minor errors!"
        )
    elif status == STATUSES.created_clean:
        messager = messages.success
        message_stub = "All Model Import Attempts were successful!"
    else:
        raise ValueError("This should never happen")

    messager(
        request,
        f"{message_stub} See {file_import_attempt._meta.verbose_name} (below) for more details.",
    )

    return HttpResponseRedirect(file_import_attempt.get_absolute_url())


def reimport_file(request, pk):
    file_importer = get_object_or_404(FileImporter, id=pk)
    return _import_file(request, file_importer)


class FileImporterCreateView(CreateView):
    model = FileImporter
    form_class = FileImporterForm
    template_name = "audits/fileimporter_form.html"

    def form_valid(self, form):
        with transaction.atomic():
            file_importer = form.save()
            return _import_file(self.request, file_importer)


def delete_file_import_models(request, pk):
    file_importer = get_object_or_404(FileImporter, id=pk)
    file_import_attempt = file_importer.most_recent_import
    num_deleted, deleted_models = file_import_attempt.delete_imported_models()

    if num_deleted:
        deleted_models_str = ", ".join(
            [
                f"{count} {model.split('.')[-1]} objects"
                for model, count in deleted_models.items()
            ]
        )
        deleted_str = f"{num_deleted} objects: {deleted_models_str}"
        messages.success(request, f"Successfully deleted {deleted_str} ")
    else:
        messages.warning(request, f"Deleted 0 objects (no objects to delete)")

    return HttpResponseRedirect(file_import_attempt.get_absolute_url())
