"""Custom django_filters.FilterSet sub-classes for cases app"""

from django.contrib.gis.measure import Distance
from django.db.models import Count
import django_filters

from watson import search as watson

from utils.layout import discover_fields
from . import models
from .form_helpers import (
    PreliminaryFacilityFilterFormHelper,
    FacilityFilterFormHelper,
    PreliminaryCaseFilterFormHelper,
    CaseFilterFormHelper,
    PersonFilterFormHelper,
    AttachmentFilterFormHelper,
    StructureFilterFormHelper,
    PreliminaryCaseGroupFilterFormHelper,
)
from .fields import PointSearchField
from .widgets import PCaseWidget


class WatsonFilter(django_filters.CharFilter):
    def filter(self, qs, value):
        return watson.filter(qs, value)


class HelpedFilterSet(django_filters.FilterSet):
    """A FilterSet with a Crispy Form Helper class"""

    def __init__(self, *args, form_helper_kwargs=None, **kwargs):
        if form_helper_kwargs is None:
            form_helper_kwargs = {}
        super(HelpedFilterSet, self).__init__(*args, **kwargs)
        self.form.helper = self.Meta.formhelper_class()
        self.form.helper.form_id = form_helper_kwargs.get(
            "form_id", self._derive_form_id()
        )
        self.form.helper.form_method = form_helper_kwargs.get("form_method", "get")
        self.form.helper.form_class = form_helper_kwargs.get(
            "form_class", "collapse show"
        )

    def _derive_form_id(self):
        return f"{self.Meta.model.__name__.lower()}-filter-form"

    class Meta:
        formhelper_class = lambda: NotImplemented


class PointFilter(django_filters.Filter):
    field_class = PointSearchField

    def filter(self, qs, value):
        if value:
            point, radius, unit = value
            return qs.filter(location__distance_lte=(point, Distance(**{unit: radius})))
        else:
            return super().filter(qs, value)


class BaseFacilityFilter(HelpedFilterSet):
    site_name = django_filters.CharFilter(lookup_expr="icontains")
    nrqz_id = django_filters.CharFilter(
        lookup_expr="icontains", label="Facility ID contains"
    )
    location = PointFilter()
    in_nrqz = django_filters.BooleanFilter(field_name="in_nrqz", label="In NRQZ")
    distance_to_gbt = django_filters.RangeFilter(
        field_name="distance_to_gbt", label="Distance to GBT (meters)"
    )
    azimuth_to_gbt = django_filters.RangeFilter(
        field_name="azimuth_to_gbt", label="Azimuth Bearing to GBT"
    )


class PreliminaryFacilityFilter(BaseFacilityFilter):
    call_sign = django_filters.CharFilter(lookup_expr="icontains")
    freq_low = django_filters.RangeFilter()
    freq_high = django_filters.RangeFilter()
    amsl = django_filters.RangeFilter()
    agl = django_filters.RangeFilter()
    structure = django_filters.CharFilter(lookup_expr="asr__exact")
    main_beam_orientation = django_filters.CharFilter(lookup_expr="icontains")
    antenna_model_number = django_filters.CharFilter(lookup_expr="icontains")
    comments = django_filters.CharFilter(lookup_expr="search")
    pcase = django_filters.ModelChoiceFilter(
        queryset=models.PreliminaryCase.objects.all(), widget=PCaseWidget()
    )

    class Meta:
        model = models.PreliminaryFacility
        formhelper_class = PreliminaryFacilityFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class FacilityFilter(BaseFacilityFilter):
    call_sign = django_filters.CharFilter(lookup_expr="icontains")
    freq_low = django_filters.RangeFilter()
    freq_high = django_filters.RangeFilter()
    amsl = django_filters.RangeFilter()
    agl = django_filters.RangeFilter()

    structure = django_filters.CharFilter(lookup_expr="asr__exact")
    main_beam_orientation = django_filters.CharFilter(lookup_expr="icontains")
    antenna_model_number = django_filters.CharFilter(lookup_expr="icontains")
    comments = django_filters.CharFilter(lookup_expr="search")
    case = django_filters.NumberFilter(label="Case Num", field_name="case__case_num")
    applicant = django_filters.CharFilter(
        field_name="case__applicant__name",
        lookup_expr="unaccent__icontains",
        label="Applicant Name",
    )
    contact = django_filters.CharFilter(
        field_name="case__contact__name",
        lookup_expr="unaccent__icontains",
        label="Contact Name",
    )
    path = django_filters.CharFilter(
        field_name="model_import_attempt__file_import_attempt__imported_from",
        lookup_expr="icontains",
        label="Imported-from Path contains",
    )
    nrao_aerpd = django_filters.RangeFilter()
    requested_max_erp_per_tx = django_filters.RangeFilter()
    search = WatsonFilter(label="Search all text fields")

    class Meta:
        model = models.Facility
        formhelper_class = FacilityFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class PreliminaryCaseGroupFilter(HelpedFilterSet):
    comments = django_filters.CharFilter(lookup_expr="search")

    class Meta:
        model = models.PreliminaryCaseGroup
        formhelper_class = PreliminaryCaseGroupFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class BaseCaseFilter(HelpedFilterSet):
    created_on = django_filters.DateFromToRangeFilter(lookup_expr="range")
    name = django_filters.CharFilter(lookup_expr="icontains")
    applicant = django_filters.CharFilter(lookup_expr="name__icontains")
    contact = django_filters.CharFilter(lookup_expr="name__icontains")
    comments = django_filters.CharFilter(lookup_expr="search")


class PreliminaryCaseFilter(BaseCaseFilter):
    class Meta:
        model = models.PreliminaryCase
        formhelper_class = PreliminaryCaseFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class CaseFilter(BaseCaseFilter):
    freq_coord = django_filters.CharFilter(lookup_expr="icontains")
    fcc_file_num = django_filters.CharFilter(lookup_expr="icontains")
    call_sign = django_filters.CharFilter(lookup_expr="icontains")
    meets_erpd_limit = django_filters.BooleanFilter(label="Meets ERPd Limit")
    sgrs_approval = django_filters.BooleanFilter(label="SGRS Approval")
    search = WatsonFilter(label="Search all text fields")
    num_facilities = django_filters.RangeFilter(label="# Facilities")

    class Meta:
        model = models.Case
        formhelper_class = CaseFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class PersonFilter(HelpedFilterSet):
    name = django_filters.CharFilter(lookup_expr="trigram_similar")
    email = django_filters.CharFilter(lookup_expr="icontains")
    phone = django_filters.CharFilter(lookup_expr="icontains")
    street = django_filters.CharFilter(lookup_expr="icontains")
    city = django_filters.CharFilter(lookup_expr="icontains")
    state = django_filters.CharFilter(lookup_expr="icontains")
    zipcode = django_filters.CharFilter(lookup_expr="icontains")
    comments = django_filters.CharFilter(lookup_expr="search")

    class Meta:
        model = models.Person
        formhelper_class = PersonFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class AttachmentFilter(HelpedFilterSet):
    path = django_filters.CharFilter(lookup_expr="icontains")
    comments = django_filters.CharFilter(lookup_expr="search")

    class Meta:
        model = models.Attachment
        formhelper_class = AttachmentFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class StructureFilter(HelpedFilterSet):
    location = PointFilter()

    class Meta:
        model = models.Structure
        formhelper_class = StructureFilterFormHelper
        fields = discover_fields(formhelper_class.layout)
