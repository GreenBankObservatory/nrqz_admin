
from django.urls import path

from . import views

urlpatterns = [
    path("cases/", views.CaseListView.as_view(), name="case_index"),
    path("cases/<int:slug>/", views.CaseDetailView.as_view(), name="case_detail"),
    path(
        "pcase-groups/",
        views.PreliminaryCaseGroupListView.as_view(),
        name="prelim_case_group_index",
    ),
    path(
        "pcase-groups/<int:pk>/",
        views.PreliminaryCaseGroupDetailView.as_view(),
        name="prelim_case_group_detail",
    ),
    path("pcases/", views.PreliminaryCaseListView.as_view(), name="prelim_case_index"),
    path(
        "pcases/<int:slug>/",
        views.PreliminaryCaseDetailView.as_view(),
        name="prelim_case_detail",
    ),
    path("structures/", views.StructureListView.as_view(), name="structure_index"),
    path(
        "structures/<int:pk>/",
        views.StructureDetailView.as_view(),
        name="structure_detail",
    ),
    path(
        "case-autocomplete/",
        views.CaseAutocompleteView.as_view(),
        name="case_autocomplete",
    ),
    path(
        "facility-autocomplete/",
        views.FacilityAutocompleteView.as_view(),
        name="facility_autocomplete",
    ),
    path("letters/", views.LetterView.as_view(), name="letters"),
    path(
        "pfacilities/",
        views.PreliminaryFacilityListView.as_view(),
        name="prelim_facility_index",
    ),
    path(
        "pfacilities/<int:pk>/",
        views.PreliminaryFacilityDetailView.as_view(),
        name="prelim_facility_detail",
    ),
    path("facilities/", views.FacilityListView.as_view(), name="facility_index"),
    path(
        "facilities/<int:pk>/",
        views.FacilityDetailView.as_view(),
        name="facility_detail",
    ),
    path(
        "facilities/<int:pk>/as_kml/", views.facility_as_kml_view, name="facility_kml"
    ),
    path("attachments/", views.AttachmentListView.as_view(), name="attachment_index"),
    path(
        "attachments/<int:pk>/",
        views.AttachmentDetailView.as_view(),
        name="attachment_detail",
    ),
    path("people/", views.PersonListView.as_view(), name="person_index"),
    path("people/<int:pk>/", views.PersonDetailView.as_view(), name="person_detail"),
    path("search/", views.SearchView.as_view(), name="search"),
]
