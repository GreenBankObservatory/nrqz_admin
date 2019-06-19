import os

from django.contrib import messages
from django.core.management import call_command
from django.db import transaction
from django.db.models import Count, Q
from django.db.utils import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotAllowed
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, UpdateView
from django.views.generic.base import RedirectView
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView

from django_import_data.views import CreateFromImportAttemptView
from django_import_data.models import FileImportBatch, FileImporter, FileImportAttempt


from cases.views import FilterTableView
from .filters import (
    FileImportAttemptFilter,
    FileImportBatchFilter,
    FileImporterFilter,
    ModelImportAttemptFilter,
)
from .tables import (
    FileImportAttemptTable,
    FileImportBatchTable,
    FileImporterTable,
    ModelImportAttemptTable,
)
from .forms import FileImporterForm
from cases.models import Case, Facility, Person, PreliminaryCase, PreliminaryFacility
from cases.forms import (
    CaseForm,
    FacilityForm,
    PersonForm,
    PreliminaryCaseForm,
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

    # def get_queryset(self):
    #     queryset = super().get_queryset()
    #     queryset = queryset.annotate(
    #         num_model_import_attempts=Count(
    #             "file_import_attempts__model_import_attempts", distinct=True
    #         )
    #     )
    #     return queryset


class FileImportAttemptListView(FilterTableView):
    table_class = FileImportAttemptTable
    filterset_class = FileImportAttemptFilter
    template_name = "audits/generic_table.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(
            num_model_import_attempts=Count("model_import_attempts"),
            is_active=Count(
                "id", distinct=True, filter=Q(model_import_attempts__is_active=True)
            ),
        )
        return queryset


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
    path = file_importer.file_path
    try:
        call_command(importer_name, path, overwrite=True, durable=True)
    except Exception as error:
        messages.error(request, f"FATAL ERROR: {error.__class__.__name__}: {error}")
        return HttpResponseRedirect(file_importer.get_absolute_url())

    file_import_attempt = file_importer.latest_file_import_attempt
    messages.success(
        request,
        f"Successfully created {file_import_attempt._meta.verbose_name} "
        f"for path {file_import_attempt.name}!",
    )

    STATUSES = file_import_attempt.STATUSES
    status = STATUSES[file_import_attempt.status]
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
        raise ValueError(f"This should never happen: status is {status}")

    messager(
        request,
        f"{message_stub} See {file_import_attempt._meta.verbose_name} (below) for more details.",
    )

    return HttpResponseRedirect(file_import_attempt.get_absolute_url())


@transaction.atomic
def _import_file_batch(request, prev_file_import_batch):
    try:
        file_import_batch = prev_file_import_batch.reimport()
    except Exception as error:
        messages.error(request, f"FATAL ERROR: {error.__class__.__name__}: {error}")
        return HttpResponseRedirect(file_import_batch.get_absolute_url())

    messages.success(
        request,
        f"Successfully deleted existing File Import Batch for paths {prev_file_import_batch.args}",
    )

    messages.success(
        request,
        f"Successfully created {file_import_batch._meta.verbose_name} "
        f"for path(s) {file_import_batch.args}!",
    )
    STATUSES = file_import_batch.STATUSES
    status = STATUSES[file_import_batch.status]
    if status == STATUSES.rejected:
        messager = messages.error
        message_stub = "However, one or more File Import Attempts failed (one or more models failed to be created)!"
    elif status == STATUSES.created_dirty:
        messager = messages.warning
        message_stub = (
            "All File Import Attempts were successful, however, "
            "one or more Model Import Attempts were created with minor errors!"
        )
    elif status == STATUSES.created_clean:
        messager = messages.success
        message_stub = "All File Import Attempts were successful!"
    else:
        raise ValueError("This should never happen")

    messager(
        request,
        f"{message_stub} See {file_import_batch._meta.verbose_name} (below) for more details.",
    )

    return HttpResponseRedirect(file_import_batch.get_absolute_url())


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
    file_import_attempt = file_importer.latest_file_import_attempt
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
        messages.warning(request, f"Deleted 0 model objects (no objects to delete)")

    return HttpResponseRedirect(file_import_attempt.get_absolute_url())


def reimport_file_batch(request, pk):
    file_import_batch = get_object_or_404(FileImportBatch, id=pk)
    return _import_file_batch(request, file_import_batch)


def delete_file_import_batch_imported_models(request, pk):
    file_import_batch = get_object_or_404(FileImportBatch, id=pk)
    num_fias_deleted, num_models_deleted, deletions = (
        file_import_batch.delete_imported_models()
    )
    if num_models_deleted:
        deleted_mias_str = ", ".join(
            [
                f"{model_deletion_count} {model.split('.')[-1]} objects"
                for model, model_deletion_count in deletions.items()
            ]
        )
        messages.success(
            request,
            f"Successfully deleted {num_fias_deleted} "
            f"File Import Attempts. {num_models_deleted} objects: {deleted_mias_str}",
        )
    else:
        messages.warning(request, f"Deleted 0 model objects (no objects to delete)")

    return HttpResponseRedirect(file_import_batch.get_absolute_url())


class FileImportAttemptExplainView(DetailView):
    model = FileImportAttempt
    template_name = "audits/render_diagrams.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form_maps = self.object.get_form_maps_used_during_import()
        context["form_maps_to_field_maps"] = {
            form_map.get_name(): form_map.field_maps for form_map in form_maps
        }
        return context


class FileImportBatchListView(FilterTableView):
    table_class = FileImportBatchTable
    filterset_class = FileImportBatchFilter
    template_name = "audits/generic_table.html"

    # def get_queryset(self):
    #     queryset = super().get_queryset()
    #     queryset = fibs.annotate(
    #         num_file_import_attempts=Count("file_import_attempts"),
    #         is_active=Count(
    #             "id",
    #             filter=Q(file_import_attempts__model_import_attempts__is_active=True),
    #         ),
    #     )
    #     return queryset


class FileImportBatchDetailView(DetailView):
    model = FileImportBatch
    template_name = "audits/fileimportbatch_detail.html"

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


def file_importer_change_path(request, pk):
    if request.method == "POST":
        file_importer = get_object_or_404(FileImporter, id=pk)
        path = request.POST.get("file_path", None)
        if not path:
            messages.error(request, "Path must be provided!")
        else:
            file_importer.file_path = path
            try:
                file_importer.save()
            except IntegrityError as error:
                if "duplicate" in error.args[0]:
                    messages.error(
                        request,
                        "Duplicate path! All paths must be unique between File Importers",
                    )
                else:
                    raise
            else:
                if not os.path.isfile(path):
                    messages.warning(
                        request,
                        f"Path has been updated to {path}. However, this path does not exist! "
                        "This should be remedied prior to reimport.",
                    )
                else:
                    messages.success(request, f"Path has been updated to {path}.")
                # We only need to refresh this one importer -- no need to waste
                # time hashing everything
                FileImporter.objects.filter(
                    id=file_importer.id
                ).refresh_from_filesystem()

    return HttpResponseRedirect(file_importer.get_absolute_url())
