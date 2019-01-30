"""Custom django_filters.FilterSet sub-classes for cases app"""

from django.contrib.gis.measure import Distance
import django_filters

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
from .fields import PointField


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
    field_class = PointField

    def filter(self, qs, value):
        if value:
            point, radius, unit = value
            return qs.filter(location__distance_lte=(point, Distance(**{unit: radius})))
        else:
            return super().filter(qs, value)


class PreliminaryFacilityFilter(HelpedFilterSet):
    site_name = django_filters.CharFilter(lookup_expr="icontains")
    nrqz_id = django_filters.CharFilter(lookup_expr="icontains")
    call_sign = django_filters.CharFilter(lookup_expr="icontains")
    freq_low = django_filters.RangeFilter()
    freq_high = django_filters.RangeFilter()
    amsl = django_filters.RangeFilter()
    agl = django_filters.RangeFilter()
    location = PointFilter()
    structure = django_filters.CharFilter(lookup_expr="asr__exact")
    main_beam_orientation = django_filters.CharFilter(lookup_expr="icontains")
    antenna_model_number = django_filters.CharFilter(lookup_expr="icontains")
    comments = django_filters.CharFilter(lookup_expr="search")

    class Meta:
        model = models.PreliminaryFacility
        formhelper_class = PreliminaryFacilityFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class FacilityFilter(HelpedFilterSet):
    site_name = django_filters.CharFilter(lookup_expr="icontains")
    nrqz_id = django_filters.CharFilter(lookup_expr="icontains")
    call_sign = django_filters.CharFilter(lookup_expr="icontains")
    freq_low = django_filters.RangeFilter()
    freq_high = django_filters.RangeFilter()
    amsl = django_filters.RangeFilter()
    agl = django_filters.RangeFilter()
    location = PointFilter()
    structure = django_filters.CharFilter(lookup_expr="asr__exact")
    main_beam_orientation = django_filters.CharFilter(lookup_expr="icontains")
    antenna_model_number = django_filters.CharFilter(lookup_expr="icontains")
    comments = django_filters.CharFilter(lookup_expr="search")

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


class PreliminaryCaseFilter(HelpedFilterSet):
    created_on = django_filters.DateFromToRangeFilter(lookup_expr="range")
    name = django_filters.CharFilter(lookup_expr="icontains")
    applicant = django_filters.CharFilter(lookup_expr="name__icontains")
    contact = django_filters.CharFilter(lookup_expr="name__icontains")
    comments = django_filters.CharFilter(lookup_expr="search")

    class Meta:
        model = models.PreliminaryCase
        formhelper_class = PreliminaryCaseFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class CaseFilter(HelpedFilterSet):
    created_on = django_filters.DateFromToRangeFilter(lookup_expr="range")
    name = django_filters.CharFilter(lookup_expr="icontains")
    applicant = django_filters.CharFilter(lookup_expr="name__unaccent__trigram_similar")
    contact = django_filters.CharFilter(lookup_expr="name__unaccent__trigram_similar")
    comments = django_filters.CharFilter(lookup_expr="search")
    freq_coord = django_filters.CharFilter(lookup_expr="icontains")
    fcc_file_num = django_filters.CharFilter(lookup_expr="icontains")
    call_sign = django_filters.CharFilter(lookup_expr="icontains")
    nrao_approval = django_filters.CharFilter()

    sgrs_approval = django_filters.CharFilter()

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
