"""URL configurations for audit app"""

from django.urls import path

from django_import_data.views import (
    RowDataDetailView,
    changed_files_view,
    acknowledge_file_import_attempt,
)

from . import views

urlpatterns = [
    path("dashboard/", views.Dashboard.as_view(), name="dashboard"),
    path(
        "file-imports/", views.FileImporterListView.as_view(), name="fileimporter_index"
    ),
    path(
        "file-imports/<int:pk>/",
        views.FileImporterDetailView.as_view(),
        name="fileimporter_detail",
    ),
    path(
        "file-imports/<int:pk>/update/",
        views.file_importer_change_path,
        name="fileimporter_update",
    ),
    path(
        "file-imports/<int:pk>/reimport/",
        views.reimport_file,
        name="fileimporter_reimport",
    ),
    path(
        "file-imports/<int:pk>/delete/",
        views.delete_file_import_models,
        name="fileimporter_delete_models",
    ),
    path(
        "file-imports/create/",
        views.FileImporterCreateView.as_view(),
        name="fileimporter_create",
    ),
    path(
        "file-import-attempts/",
        views.FileImportAttemptListView.as_view(),
        name="fileimportattempt_index",
    ),
    path(
        "file-import-attempts/<int:pk>/",
        views.FileImportAttemptDetailView.as_view(),
        name="fileimportattempt_detail",
    ),
    path(
        "file-import-attempts/<int:pk>/explain",
        views.FileImportAttemptExplainView.as_view(),
        name="fileimportattempt_explain",
    ),
    path(
        "file-import-attempts/<int:pk>/acknowledge",
        acknowledge_file_import_attempt,
        name="acknowledge_fileimportattempt",
    ),
    path(
        "changed-file-import-attempts/",
        changed_files_view,
        name="changed_file_import_attempts",
    ),
    path(
        "file-import-batches/",
        views.FileImportBatchListView.as_view(),
        name="fileimportbatch_index",
    ),
    path(
        "file-import-batches/<int:pk>/",
        views.FileImportBatchDetailView.as_view(),
        name="fileimportbatch_detail",
    ),
    path(
        "file-import-batches/<int:pk>/delete/",
        views.delete_file_import_batch_imported_models,
        name="fileimportbatch_delete_models",
    ),
    path(
        "file-import-batches/<int:pk>/reimport/",
        views.reimport_file_batch,
        name="fileimportbatch_reimport",
    ),
    path(
        "model-imports/",
        views.ModelImportAttemptListView.as_view(),
        name="modelimportattempt_index",
    ),
    path(
        "model-imports/<int:pk>/",
        views.ModelImportAttemptDetailView.as_view(),
        name="modelimportattempt_detail",
    ),
    # path("row-data/", views.RowDataListView.as_view(), name="rowdata_list"),
    path("row-data/<int:pk>/", RowDataDetailView.as_view(), name="rowdata_detail"),
    path(
        "person/create-from-audit/<int:attempt_pk>/",
        views.PersonCreateFromAuditView.as_view(),
        name="person_create_from_audit",
    ),
    path(
        "cases/create-from-audit/<int:attempt_pk>/",
        views.CaseCreateFromAuditView.as_view(),
        name="case_create_from_audit",
    ),
    path(
        "facilities/create-from-audit/<int:attempt_pk>/",
        views.FacilityCreateFromAuditView.as_view(),
        name="facility_create_from_audit",
    ),
    path(
        "pfacilities/create-from-audit/<int:attempt_pk>/",
        views.PFacilityCreateFromAuditView.as_view(),
        name="preliminaryfacility_create_from_audit",
    ),
    path(
        "pcases/create-from-audit/<int:attempt_pk>/",
        views.PCaseCreateFromAuditView.as_view(),
        name="preliminarycase_create_from_audit",
    ),
]
