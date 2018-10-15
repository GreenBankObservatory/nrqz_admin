from django.urls import path

from . import views

urlpatterns = [
    path("batches/", views.BatchListView.as_view(), name="batch_index"),
    path("batches/<int:pk>/", views.BatchDetailView.as_view(), name="batch_detail"),
    path("submissions/", views.SubmissionListView.as_view(), name="submission_index"),
    path("submissions/<int:pk>/", views.SubmissionDetailView.as_view(), name="submission_detail"),
    path(
        "facilities/",
        views.FacilityListView.as_view(),
        name="facility_index",
    ),
    path(
        "facilities/<int:pk>/",
        views.FacilityDetailView.as_view(),
        name="facility_detail",
    ),
    path(
        "attachments/",
        views.AttachmentListView.as_view(),
        name="attachment_index",
    ),
    path(
        "attachments/<int:pk>/",
        views.AttachmentDetailView.as_view(),
        name="attachment_detail",
    ),
]
