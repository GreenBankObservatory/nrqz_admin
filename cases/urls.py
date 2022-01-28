from django.urls import path

from . import views
from . import autocomplete_views

urlpatterns = [
    path(
        "attachment-dashboard/",
        views.AttachmentDashboard.as_view(),
        name="attachment_dashboard",
    ),
    path("cases/", views.CaseListView.as_view(), name="case_index"),
    path("cases/create", views.CaseCreateView.as_view(), name="case_create"),
    path("cases/<str:slug>/", views.CaseDetailView.as_view(), name="case_detail"),
    path("cases/<str:slug>/edit", views.CaseUpdateView.as_view(), name="case_update"),
    path("cases/<int:pk>/as_kml/", views.case_as_kml_view, name="case_kml"),
    path("case-groups/", views.CaseGroupListView.as_view(), name="case_group_index"),
    path(
        "case-groups/<int:pk>/",
        views.CaseGroupDetailView.as_view(),
        name="case_group_detail",
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
        autocomplete_views.CaseAutocompleteView.as_view(),
        name="case_autocomplete",
    ),
    path(
        "casegroup-autocomplete/",
        autocomplete_views.CaseGroupAutocompleteView.as_view(),
        name="casegroup_autocomplete",
    ),
    path(
        "pcase-autocomplete/",
        autocomplete_views.PreliminaryCaseAutocompleteView.as_view(),
        name="pcase_autocomplete",
    ),
    path(
        "facility-autocomplete/",
        autocomplete_views.FacilityAutocompleteView.as_view(),
        name="facility_autocomplete",
    ),
    path(
        "pfacility-autocomplete/",
        autocomplete_views.PreliminaryFacilityAutocompleteView.as_view(),
        name="pfacility_autocomplete",
    ),
    path("letters/", views.LetterView.as_view(), name="letters"),
    path("letters-simple/", views.LetterViewSimple.as_view(), name="letters_simple"),
    path("letters-fancy/", views.LetterHtmlView.as_view(), name="letters_fancy"),
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
    path(
        "attachment-autocomplete/",
        autocomplete_views.AttachmentAutocompleteView.as_view(),
        name="attachment_autocomplete",
    ),
    path("people/", views.PersonListView.as_view(), name="person_index"),
    path("people/<int:pk>/", views.PersonDetailView.as_view(), name="person_detail"),
    path("people/create", views.PersonCreateView.as_view(), name="person_create"),
    path(
        "people/<int:pk>/edit", views.PersonUpdateView.as_view(), name="person_update"
    ),
    path(
        "people/<int:pk>/merge", views.merge_similar_people, name="merge_similar_people"
    ),
    path(
        "person-autocomplete/",
        autocomplete_views.PersonAutocompleteView.as_view(),
        name="person_autocomplete",
    ),
    path("search/", views.SearchView.as_view(), name="search"),
    path("cases/<str:case_num>/duplicate", views.duplicate_case, name="duplicate_case"),
]
