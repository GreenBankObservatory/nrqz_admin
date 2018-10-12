from django.urls import path

from . import views


urlpatterns = [
    path("", views.ApplicantListView.as_view(), name="applicant_index"),
    path("<int:pk>", views.ApplicantDetailView.as_view(), name="applicant_detail"),
]
