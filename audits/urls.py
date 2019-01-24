"""URL configurations for audit app"""

from django.urls import path

from django_import_data.views import (
    FileImporterListView,
    FileImporterDetailView,
    FileImportAttemptListView,
    FileImportAttemptDetailView,
    ModelImportAttemptListView,
    ModelImportAttemptDetailView,
    RowDataListView,
    RowDataDetailView,
)

from . import views

urlpatterns = [
    path(
        "file-imports/", views.FileImporterListView.as_view(), name="fileimporter_list"
    ),
    path(
        "file-imports/<int:pk>/",
        views.FileImporterDetailView.as_view(),
        name="fileimporter_detail",
    ),
    path(
        "file-imports/<int:pk>/reimport",
        views.reimport_file,
        name="fileimporter_reimport",
    ),
    path(
        "file-import-attempts/",
        views.FileImportAttemptListView.as_view(),
        name="fileimportattempt_list",
    ),
    path(
        "file-import-attempts/<int:pk>/",
        views.FileImportAttemptDetailView.as_view(),
        name="fileimportattempt_detail",
    ),
    path(
        "model-imports/",
        views.ModelImportAttemptListView.as_view(),
        name="modelimportattempt_list",
    ),
    path(
        "model-imports/<int:pk>/",
        ModelImportAttemptDetailView.as_view(),
        name="modelimportattempt_detail",
    ),
    # path("row-data/", views.RowDataListView.as_view(), name="rowdata_list"),
    # path("row-data/<int:pk>/", RowDataDetailView.as_view(), name="rowdata_detail"),
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
