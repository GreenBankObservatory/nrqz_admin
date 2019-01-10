"""URL configurations for audit app"""

from django.urls import path

from django_import_data.views import (
    GenericAuditGroupBatchListView,
    GenericAuditGroupBatchDetailView,
    GenericBatchImportListView,
    GenericBatchImportDetailView,
    GenericAuditGroupDetailView,
    GenericAuditGroupListView,
    GenericAuditListView,
    GenericAuditDetailView,
    RowDataListView,
    RowDataDetailView,
)

from . import views

urlpatterns = [
    path(
        "batches/",
        views.GenericAuditGroupBatchListView.as_view(),
        name="genericauditgroupbatch_list",
    ),
    path(
        "batches/<int:pk>/",
        GenericAuditGroupBatchDetailView.as_view(),
        name="genericauditgroupbatch_detail",
    ),
    path(
        "batch-imports/",
        views.GenericBatchImportListView.as_view(),
        name="genericbatchimport_list",
    ),
    path(
        "batch-imports/<int:pk>/",
        views.GenericBatchImportDetailView.as_view(),
        name="genericbatchimport_detail",
    ),
    path("audits/", views.GenericAuditListView.as_view(), name="genericaudit_list"),
    path(
        "audits/<int:pk>/", GenericAuditDetailView.as_view(), name="genericaudit_detail"
    ),
    path(
        "audit-groups/",
        views.GenericAuditGroupListView.as_view(),
        name="genericauditgroup_list",
    ),
    path("row-data/", views.RowDataListView.as_view(), name="rowdata_list"),
    path("row-data/<int:pk>/", RowDataDetailView.as_view(), name="rowdata_detail"),
    path(
        "audit-groups/<int:pk>/",
        views.GenericAuditGroupDetailView.as_view(),
        name="genericauditgroup_detail",
    ),
    path(
        "person/create-from-audit/<int:audit_pk>/",
        views.PersonCreateFromAuditView.as_view(),
        name="person_create_from_audit",
    ),
    path(
        "cases/create-from-audit/<int:audit_pk>/",
        views.CaseCreateFromAuditView.as_view(),
        name="case_create_from_audit",
    ),
    path(
        "facilities/create-from-audit/<int:audit_pk>/",
        views.FacilityCreateFromAuditView.as_view(),
        name="facility_create_from_audit",
    ),
    path(
        "pfacilities/create-from-audit/<int:audit_pk>/",
        views.PFacilityCreateFromAuditView.as_view(),
        name="preliminaryfacility_create_from_audit",
    ),
    path(
        "pcases/create-from-audit/<int:audit_pk>/",
        views.PCaseCreateFromAuditView.as_view(),
        name="preliminarycase_create_from_audit",
    ),
]
