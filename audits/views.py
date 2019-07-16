import os

from django.contrib import messages
from django.core.management import call_command
from django.db import transaction
from django.db.utils import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView
from django.views.generic.base import RedirectView
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import ProcessFormView

from django_tables2.views import SingleTableMixin, MultiTableMixin
from django_import_data.views import CreateFromImportAttemptView
from django_import_data.models import (
    FileImporterBatch,
    FileImporter,
    FileImportAttempt,
    ModelImportAttempt,
    ModelImporter,
    RowData,
)


from cases.views import FilterTableView
from .filters import (
    FileImportAttemptFilter,
    FileImporterBatchFilter,
    FileImporterFilter,
    ModelImportAttemptFilter,
    ModelImporterFilter,
    RowDataFilter,
)
from .tables import (
    FileImportAttemptTable,
    FileImporterBatchTable,
    FileImporterDashboardTable,
    FileImporterTable,
    ModelImportAttemptTable,
    ModelImporterTable,
    RowDataTable,
    FileImporterErrorSummaryTable,
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

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate_num_file_import_attempts()
        queryset = queryset.annotate_num_model_importers()
        return queryset


class FileImportAttemptListView(FilterTableView):
    table_class = FileImportAttemptTable
    filterset_class = FileImportAttemptFilter
    template_name = "audits/generic_table.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate_num_model_importers()
        return queryset


class FileImporterDetailView(MultiTableMixin, DetailView):
    model = FileImporter
    tables = [FileImportAttemptTable, FileImporterErrorSummaryTable, RowDataTable]
    template_name = "audits/fileimporter_detail.html"
    table_pagination = {"per_page": 10}

    def get_tables_data(self):
        fia_filter_qs = FileImportAttemptFilter(
            self.request.GET,
            queryset=self.object.file_import_attempts.all().annotate_num_model_importers(),
            form_helper_kwargs={"form_class": "collapse"},
        ).qs
        error_table_data = self.object.condensed_errors_by_row_as_dicts()
        rd_filter_qs = RowDataFilter(
            self.request.GET,
            queryset=RowData.objects.get_rejected()
            .filter(file_import_attempt=self.object.latest_file_import_attempt.id)
            .annotate_num_model_importers()
            .annotate_current_status(),
            form_helper_kwargs={"form_class": "collapse"},
        ).qs
        return [fia_filter_qs, error_table_data, rd_filter_qs]

    def get_object(self, *args, **kwargs):
        instance = super().get_object(*args, **kwargs)
        # Refresh the file info from disk
        instance.refresh_from_filesystem()
        return instance


class ModelImporterDetailView(MultiTableMixin, DetailView):
    model = ModelImporter
    tables = [ModelImportAttemptTable]
    template_name = "audits/modelimporter_detail.html"

    def get_tables_data(self):
        mia_filter_qs = ModelImportAttemptFilter(
            self.request.GET,
            queryset=self.object.model_import_attempts.all(),
            form_helper_kwargs={"form_class": "collapse"},
        ).qs
        return [mia_filter_qs]


class ModelImporterListView(FilterTableView):
    table_class = ModelImporterTable
    filterset_class = ModelImporterFilter
    template_name = "audits/modelimporter_index.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate_num_model_import_attempts()
        return queryset


class RowDataListView(FilterTableView):
    table_class = RowDataTable
    filterset_class = RowDataFilter
    template_name = "audits/rowdata_index.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate_num_model_importers()
        return queryset


class RowDataDetailView(SingleTableMixin, DetailView):
    model = RowData
    table_class = ModelImporterTable
    template_name = "audits/rowdata_detail.html"
    table_pagination = {"per_page": 10}

    def get_table_data(self):
        return self.object.model_importers.all().annotate_num_model_import_attempts()


class ModelImportAttemptDetailView(DetailView):
    model = ModelImportAttempt
    template_name = "audits/modelimportattempt_detail.html"


class ModelImportAttemptListView(FilterTableView):
    table_class = ModelImportAttemptTable
    filterset_class = ModelImportAttemptFilter
    template_name = "audits/generic_table.html"


class FileImportAttemptDetailView(MultiTableMixin, DetailView):
    model = FileImportAttempt
    tables = [RowDataTable]
    template_name = "audits/fileimportattempt_detail.html"
    table_pagination = {"per_page": 10}

    def get_tables_data(self):
        rd_filter_qs = RowDataFilter(
            self.request.GET,
            queryset=RowData.objects.filter(
                file_import_attempt=self.object.id
            ).annotate_num_model_importers(),
            form_helper_kwargs={"form_class": "collapse"},
        ).qs
        return [rd_filter_qs]

    def get_object(self, *args, **kwargs):
        instance = super().get_object(*args, **kwargs)
        # Refresh the latest file hash from disk. Or, if not found
        instance.file_importer.refresh_from_filesystem()
        instance.refresh_from_db()
        return instance


@transaction.atomic
def _import_file(request, importer_name, path, on_error=None):
    if on_error is None:
        on_error = reverse("fileimporter_create")
    try:
        call_command(importer_name, path, overwrite=True, durable=True, propagate=True)
    except Exception as error:
        messages.error(request, f"FATAL ERROR: {error.__class__.__name__}: {error}")
        # Manually set rollback since we aren't raising an Exception here
        transaction.set_rollback(True)
        return HttpResponseRedirect(on_error)

    file_importer = get_object_or_404(
        FileImporter, importer_name=importer_name, file_path=path
    )
    file_import_attempt = file_importer.latest_file_import_attempt
    # file_import_attempt.save()
    mias = ModelImportAttempt.objects.filter(
        model_importer__row_data__file_import_attempt=file_import_attempt.id
    )
    mias.derive_values()
    file_import_attempt.refresh_from_db()
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
    elif status == STATUSES.empty:
        messager = messages.error
        message_stub = "However, no Model Import Attempts were created (empty file)!"
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
def _import_file_batch(request, prev_file_importer_batch, on_error=None):
    if on_error is None:
        on_error = "/"
    try:
        file_importer_batch = prev_file_importer_batch.reimport()
    except ValueError as error:
        messages.error(request, f"FATAL ERROR: {error.__class__.__name__}: {error}")
        # Manually set rollback since we aren't raising an Exception here
        transaction.set_rollback(True)
        return HttpResponseRedirect(on_error)

    messages.success(
        request,
        f"Successfully deleted existing File Importer Batch for paths {prev_file_importer_batch.args}",
    )

    messages.success(
        request,
        f"Successfully created {file_importer_batch._meta.verbose_name} "
        f"for path(s) {file_importer_batch.args}!",
    )
    STATUSES = file_importer_batch.STATUSES
    status = STATUSES[file_importer_batch.status]
    if status == STATUSES.rejected:
        messager = messages.error
        message_stub = "However, one or more File Import Attempts failed (one or more models failed to be created)!"
    elif status == STATUSES.empty:
        messager = messages.error
        message_stub = (
            "However, one or more File Import Attempts failed (no models were created)!"
        )
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

        raise ValueError(f"This should never happen: got status {status}")

    messager(
        request,
        f"{message_stub} See {file_importer_batch._meta.verbose_name} (below) for more details.",
    )

    return HttpResponseRedirect(file_importer_batch.get_absolute_url())


def reimport_file(request, pk):
    file_importer = get_object_or_404(FileImporter, id=pk)
    importer_name = file_importer.importer_name
    path = file_importer.file_path
    return _import_file(
        request,
        importer_name=importer_name,
        path=path,
        on_error=file_importer.get_absolute_url(),
    )


class FileImporterCreateView(CreateView):
    model = FileImporter
    form_class = FileImporterForm
    template_name = "audits/fileimporter_form.html"

    def form_valid(self, form):
        with transaction.atomic():
            return _import_file(
                self.request,
                importer_name=form.data["importer_name"],
                path=form.data["file_path"],
            )


def delete_file_import_models(request, pk):
    file_importer = get_object_or_404(FileImporter, id=pk)
    # file_import_attempt = file_importer.latest_file_import_attempt
    total_num_fia_deletions, total_num_mia_deletions, all_mia_deletions = (
        file_importer.delete_imported_models()
    )

    if total_num_mia_deletions:
        deleted_models_str = ", ".join(
            [
                f"{count} {model.split('.')[-1]} objects"
                for model, count in all_mia_deletions.items()
            ]
        )
        deleted_str = f"{total_num_mia_deletions} objects: {deleted_models_str}"
        messages.success(request, f"Successfully deleted {deleted_str} ")
    else:
        messages.warning(request, f"Deleted 0 model objects (no objects to delete)")

    return HttpResponseRedirect(file_importer.get_absolute_url())


def reimport_file_batch(request, pk):
    file_importer_batch = get_object_or_404(FileImporterBatch, id=pk)
    return _import_file_batch(
        request, file_importer_batch, on_error=file_importer_batch.get_absolute_url()
    )


def delete_file_importer_batch_imported_models(request, pk):
    file_importer_batch = get_object_or_404(FileImporterBatch, id=pk)
    num_fias_deleted, num_models_deleted, deletions = (
        file_importer_batch.delete_imported_models()
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

    return HttpResponseRedirect(file_importer_batch.get_absolute_url())


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


class FileImporterBatchListView(FilterTableView):
    table_class = FileImporterBatchTable
    filterset_class = FileImporterBatchFilter
    template_name = "audits/generic_table.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate_num_file_importers()
        queryset = queryset.annotate_num_successful_file_importers()
        queryset = queryset.annotate_num_failed_file_importers()
        return queryset


class FileImporterBatchDetailView(SingleTableMixin, DetailView):
    model = FileImporterBatch
    template_name = "audits/fileimporterbatch_detail.html"
    table_class = FileImporterTable
    table_pagination = {"per_page": 10}

    def get_table_data(self):
        fi_filter_qs = FileImporterFilter(
            self.request.GET,
            queryset=self.object.file_importers.all()
            .annotate_num_file_import_attempts()
            .annotate_num_model_importers(),
        ).qs
        return fi_filter_qs


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
                file_importer.refresh_from_filesystem()

    return HttpResponseRedirect(file_importer.get_absolute_url())


class FileImporterDashboard(SingleTableMixin, TemplateView, ProcessFormView):
    table_class = FileImporterDashboardTable
    template_name = "audits/file_importer_dashboard.html"
    table_pagination = {"per_page": 10}

    def get_queryset(self):
        queryset = FileImporter.objects.all()
        queryset = queryset.annotate_current_status()
        queryset = queryset.annotate_num_model_importers()
        queryset = queryset.annotate_num_file_import_attempts()

        return queryset.exclude(
            current_status=FileImportAttempt.CURRENT_STATUSES.acknowledged.db_value
        ).filter(
            status__in=[
                FileImporter.STATUSES.rejected.db_value,
                FileImporter.STATUSES.created_dirty.db_value,
                FileImporter.STATUSES.empty.db_value,
            ]
        )

    @transaction.atomic
    def dispatch(self, request, *args, **kwargs):
        if request.method == "POST":
            acknowledge_all = request.POST.get("all", None)
            if acknowledge_all:
                file_importers = self.get_queryset().all()
            else:
                file_importer_ids = request.POST.getlist("check", None)
                file_importers = FileImporter.objects.filter(id__in=file_importer_ids)

            # Get count here, since QS will be empty soon
            num_file_importers = file_importers.count()
            # Convert to string here, since this QS will be empty soon. We rely
            # on Django to concatenate the values list string to a reasonable length,
            # so we don't have to worry about doing it ourselves
            fi_str = str(file_importers.values_list("id", flat=True))
            for file_importer in file_importers.all():
                file_importer.acknowledge()
            if num_file_importers:
                messages.success(
                    request,
                    f"Successfully acknowledged {num_file_importers} File Importers: {fi_str}",
                )
            else:
                messages.warning(
                    request, "No File Importers selected for acknowledgement"
                )
            return HttpResponseRedirect(reverse("dashboard"))

        return super().dispatch(request, *args, **kwargs)
