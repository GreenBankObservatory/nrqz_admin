"""URL configurations for audit app"""

from django.urls import path

from django_import_data.views import changed_files_view, acknowledge_file_importer

from . import views

urlpatterns = [
    path(
        "file-dashboard/", views.FileImporterDashboard.as_view(), name="file_dashboard"
    ),
    path(
        "unimported-files-dashboard/",
        views.UnimportedFilesDashboard.as_view(),
        name="unimported_files_dashboard",
    ),
    path(
        "orphaned-files-dashboard/",
        views.OrphanedFilesDashboard.as_view(),
        name="orphaned_files_dashboard",
    ),
    path(
        "file-importers/",
        views.FileImporterListView.as_view(),
        name="fileimporter_index",
    ),
    path(
        "file-importers/<int:pk>/",
        views.FileImporterDetailView.as_view(),
        name="fileimporter_detail",
    ),
    path(
        "file-importers/<int:pk>/update/",
        views.file_importer_change_path,
        name="fileimporter_update",
    ),
    path(
        "file-importers/<int:pk>/reimport/",
        views.reimport_file,
        name="fileimporter_reimport",
    ),
    path(
        "file-importers/<int:pk>/recheck/",
        views.recheck_file,
        name="fileimporter_recheck",
    ),
    path(
        "file-importers/<int:pk>/delete/",
        views.delete_file_import_models,
        name="fileimporter_delete_models",
    ),
    path(
        "file-importers/create/",
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
        "file-importer/<int:pk>/acknowledge",
        acknowledge_file_importer,
        name="acknowledge_fileimporter",
    ),
    path(
        "changed-file-import-attempts/",
        changed_files_view,
        name="changed_file_import_attempts",
    ),
    path(
        "file-importer-batches/",
        views.FileImporterBatchListView.as_view(),
        name="fileimporterbatch_index",
    ),
    path(
        "file-importer-batches/<int:pk>/",
        views.FileImporterBatchDetailView.as_view(),
        name="fileimporterbatch_detail",
    ),
    path(
        "file-importer-batches/<int:pk>/delete/",
        views.delete_file_importer_batch_imported_models,
        name="fileimporterbatch_delete_models",
    ),
    path(
        "file-importer-batches/<int:pk>/reimport/",
        views.reimport_file_batch,
        name="fileimporterbatch_reimport",
    ),
    path(
        "model-importers/",
        views.ModelImporterListView.as_view(),
        name="modelimporter_index",
    ),
    path(
        "model-importers/<int:pk>/",
        views.ModelImporterDetailView.as_view(),
        name="modelimporter_detail",
    ),
    path(
        "model-import-attempts/",
        views.ModelImportAttemptListView.as_view(),
        name="modelimportattempt_index",
    ),
    path(
        "model-import-attempts/<int:pk>/",
        views.ModelImportAttemptDetailView.as_view(),
        name="modelimportattempt_detail",
    ),
    path("row-data/", views.RowDataListView.as_view(), name="rowdata_index"),
    path(
        "row-data/<int:pk>/", views.RowDataDetailView.as_view(), name="rowdata_detail"
    ),
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
