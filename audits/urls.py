"""URL configurations for audit app"""

from django.urls import path

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
]
