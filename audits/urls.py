"""URL configurations for audit app"""

from django.urls import path

from django_import_data.views import (
    FileImportAttemptDetailView,
    FileImportAttemptListView,
    FileImporterDetailView,
    FileImporterListView,
    ModelImportAttemptDetailView,
    ModelImportAttemptListView,
    RowDataDetailView,
    RowDataListView,
)

from . import views

urlpatterns = [
    path(
        "file-imports/", views.FileImporterListView.as_view(), name="fileimporter_index"
    ),
    path(
        "file-imports/<int:pk>/",
        views.FileImporterDetailView.as_view(),
        name="fileimporter_detail",
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
        "model-imports/",
        views.ModelImportAttemptListView.as_view(),
        name="modelimportattempt_index",
    ),
    path(
        "model-imports/<int:pk>/",
        ModelImportAttemptDetailView.as_view(),
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
