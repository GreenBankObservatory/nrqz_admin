from django.urls import path

from . import views

urlpatterns = [
    path("batches/", views.BatchListView.as_view(), name="batch_index"),
    path("batches/<int:pk>/", views.BatchDetailView.as_view(), name="batch_detail"),
    path("cases/", views.CaseListView.as_view(), name="case_index"),
    path("cases/<int:pk>/", views.CaseDetailView.as_view(), name="case_detail"),
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
    path("people/", views.PersonListView.as_view(), name="person_index"),
    path("people/<int:pk>/", views.PersonDetailView.as_view(), name="person_detail"),

]