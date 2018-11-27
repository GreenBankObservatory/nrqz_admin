"""URL configurations for audit app"""

from django.urls import path

from . import views

urlpatterns = [
    path("batches/", views.BatchAuditListView.as_view(), name="batch_audit_index"),
    path(
        "batches/<int:pk>/",
        views.BatchAuditDetailView.as_view(),
        name="batch_audit_detail",
    ),
]
