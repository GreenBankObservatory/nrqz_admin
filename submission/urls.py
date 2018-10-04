from django.urls import path

from . import views

urlpatterns = [
    path("", views.SubmissionListView.as_view(), name="submission_index"),
    path("<int:pk>", views.SubmissionDetailView.as_view(), name="submission_detail"),
    # path(
    #     "facilities/",
    #     views.FacilityListView.as_view(),
    #     name="submission_facility_index",
    # ),
    path("facilities/", views.facility_list),
    path(
        "facilities/<int:pk>/",
        views.FacilityDetailView.as_view(),
        name="submission_facility_detail",
    ),
    path(
        "attachments/",
        views.AttachmentListView.as_view(),
        name="submission_attachment_index",
    ),
    path(
        "attachments/<int:pk>/",
        views.AttachmentDetailView.as_view(),
        name="submission_attachment_detail",
    ),
]
