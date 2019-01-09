"""URL configurations for audit app"""

from django.urls import path

from django_import_data.views import (
    GenericAuditGroupDetailView,
    GenericAuditGroupListView,
    GenericAuditListView,
    GenericAuditDetailView,
    RowDataListView,
    RowDataDetailView,
)

from . import views

urlpatterns = [
    path("batches/", views.BatchAuditListView.as_view(), name="batch_audit_index"),
    path(
        "groups/batches/",
        views.BatchAuditGroupListView.as_view(),
        name="batch_audit_group_index",
    ),
    path(
        "batches/<int:pk>/",
        views.BatchAuditDetailView.as_view(),
        name="batch_audit_detail",
    ),
    path(
        "groups/batches/<int:pk>/",
        views.BatchAuditGroupDetailView.as_view(),
        name="batch_audit_group_detail",
    ),
    path(
        "batches/create",
        views.BatchAuditCreateView.as_view(),
        name="batch_audit_create",
    ),
    path("audits/", GenericAuditListView.as_view(), name="genericaudit_list"),
    path(
        "audits/<int:pk>/", GenericAuditDetailView.as_view(), name="genericaudit_detail"
    ),
    path(
        "audit-groups/",
        GenericAuditGroupListView.as_view(),
        name="genericauditgroup_list",
    ),
    path("row-data/", views.RowDataListView.as_view(), name="rowdata_list"),
    path("row-data/<int:pk>/", RowDataDetailView.as_view(), name="rowdata_detail"),
    path(
        "audit-groups/<int:pk>/",
        GenericAuditGroupDetailView.as_view(),
        name="genericauditgroup_detail",
    ),
    # path(
    #     "<str:model>/create-from-audit/<int:audit_pk>/",
    #     views.CreateFromAuditRedirectView.as_view(),
    #     name="create_from_audit",
    # ),
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
