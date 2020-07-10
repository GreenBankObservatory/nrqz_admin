"""Custom django_filters.FilterSet sub-classes for cases app"""

from django import forms
from django.contrib.gis.measure import Distance
from django.db.models import Q

import django_filters
from django_import_data.numranges import (
    range_notation_to_list_of_ranges,
    get_nums_from_str,
)
from watson import search as watson

from utils.layout import discover_fields
from . import models
from .form_helpers import (
    AttachmentFilterFormHelper,
    CaseFilterFormHelper,
    CaseGroupFilterFormHelper,
    FacilityFilterFormHelper,
    PersonFilterFormHelper,
    PreliminaryCaseFilterFormHelper,
    PreliminaryFacilityFilterFormHelper,
    StructureFilterFormHelper,
)
from .fields import PointSearchField
from .widgets import PCaseWidget


class RangeNotationField(forms.CharField):
    default_error_messages = {
        "invalid_range": 'Range query must be in the format "1,2,3-4".'
    }

    def clean(self, value):
        if value:
            # value = REP.sub("", value)
            try:
                value = range_notation_to_list_of_ranges(value)
            except ValueError as error:
                print(f"RangeNotationField: Invalid range: {value}\nERROR: {error}")
                raise forms.ValidationError(
                    self.error_messages["invalid_range"], code="invalid_range"
                )
        return value


class RangeNotationFilter(django_filters.CharFilter):
    """A range filter that parses range-notation strings to generate range filters

    e.g. 1,3-5 would yield a query of Q(<field_name>__gte=1, <field_name>__lte=1) |
    Q(<field_name>__gte=3, <field_name>__lte=5)
    """

    field_class = RangeNotationField

    def filter(self, qs, num_ranges, inclusive=True):
        if num_ranges is not None:
            # Start with an empty query
            filtered_by_range = Q()
            # Then, for every range in the derived ranges...
            for range_ in num_ranges:
                # ...filter for all values that are between its bounds

                try:
                    range_start, range_end = range_
                except ValueError:
                    # If we can't unpack, then we treat the value as atomic --
                    # that is, as a non-range item -- and use it for an
                    # "exact" query
                    value = range_
                    filtered_by_range |= Q(**{self.field_name: value})
                else:
                    # If we have successfully unpacked our range, we use its
                    # boundaries to perform our range query (respecting the
                    # inclusive argument)
                    filtered_by_range |= Q(
                        **{
                            f"{self.field_name}__gt{'e' if inclusive else ''}": range_start,
                            f"{self.field_name}__lt{'e' if inclusive else ''}": range_end,
                        }
                    )

            # Finally, apply the filter we just built to the existing queryset and return
            return qs.filter(filtered_by_range)
        return qs


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
        print("PointFilter value", value)

        if value:
            point, radius, unit = value
            print("PointFilter point, radius, unit", point, radius, unit)
            return qs.filter(location__distance_lte=(point, Distance(**{unit: radius})))
        else:
            return super().filter(qs, value)


class BaseFacilityFilter(HelpedFilterSet):
    try:
        _boundaries = models.Boundaries.objects.get(name="NRQZ")
    except models.Boundaries.DoesNotExist:
        raise ValueError("No NRQZ boundaries! Did you run the DB init script?")
    site_name = django_filters.CharFilter(lookup_expr="icontains")
    nrqz_id = django_filters.CharFilter(
        lookup_expr="icontains", label="Facility ID contains"
    )
    location = PointFilter(boundaries=_boundaries)
    in_nrqz = django_filters.BooleanFilter(field_name="in_nrqz", label="In NRQZ")
    distance_to_gbt = RangeNotationFilter(
        field_name="distance_to_gbt", label="Distance to GBT (meters)"
    )
    azimuth_to_gbt = RangeNotationFilter(
        field_name="azimuth_to_gbt", label="Azimuth Bearing to GBT"
    )


class PreliminaryFacilityFilter(BaseFacilityFilter):
    call_sign = django_filters.CharFilter(lookup_expr="icontains")
    freq_low = RangeNotationFilter()
    freq_high = RangeNotationFilter()
    amsl = RangeNotationFilter()
    agl = RangeNotationFilter()
    structure = django_filters.CharFilter(lookup_expr="asr__exact")
    main_beam_orientation = django_filters.CharFilter(lookup_expr="icontains")
    antenna_model_number = django_filters.CharFilter(lookup_expr="icontains")
    comments = django_filters.CharFilter(lookup_expr="search")
    pcase = RangeNotationFilter()

    class Meta:
        model = models.PreliminaryFacility
        formhelper_class = PreliminaryFacilityFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class FacilityFilter(BaseFacilityFilter):
    call_sign = django_filters.CharFilter(lookup_expr="icontains")
    freq_low = RangeNotationFilter()
    freq_high = RangeNotationFilter()
    amsl = RangeNotationFilter()
    agl = RangeNotationFilter()
    bandwidth = RangeNotationFilter()

    structure = django_filters.CharFilter(lookup_expr="asr__exact")
    main_beam_orientation = django_filters.CharFilter(lookup_expr="icontains")
    antenna_model_number = django_filters.CharFilter(lookup_expr="icontains")
    # comments = django_filters.CharFilter(lookup_expr="search")
    case = RangeNotationFilter(label="Case Num", field_name="case__case_num")
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
    imported_from = django_filters.CharFilter(
        field_name="model_import_attempt__model_importer__row_data__file_import_attempt__imported_from",
        lookup_expr="icontains",
        label="Imported-from Path contains",
    )
    nrao_aerpd = RangeNotationFilter()
    requested_max_erp_per_tx = RangeNotationFilter()
    search = WatsonFilter(label="Search all text fields")
    si_done = django_filters.DateFromToRangeFilter(label="SI Done (date from, date to)")
    agency_num = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = models.Facility
        formhelper_class = FacilityFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class CaseGroupFilter(HelpedFilterSet):
    id = RangeNotationFilter(label="CG ID")
    comments = django_filters.CharFilter(lookup_expr="search")
    num_cases = RangeNotationFilter(label="# Cases")
    num_pcases = RangeNotationFilter(label="# Prelim. Cases")
    completed = django_filters.BooleanFilter(label="Completed")

    class Meta:
        model = models.CaseGroup
        formhelper_class = CaseGroupFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class BaseCaseFilter(HelpedFilterSet):
    created_on = django_filters.DateFromToRangeFilter(lookup_expr="range")
    applicant = django_filters.CharFilter(lookup_expr="name__icontains")
    contact = django_filters.CharFilter(lookup_expr="name__icontains")
    comments = django_filters.CharFilter(lookup_expr="search")


class PreliminaryCaseFilter(BaseCaseFilter):
    case_num = RangeNotationFilter()

    class Meta:
        model = models.PreliminaryCase
        formhelper_class = PreliminaryCaseFilterFormHelper
        fields = discover_fields(formhelper_class.layout)


class CaseFilter(BaseCaseFilter):
    case_num = RangeNotationFilter()
    freq_coord = django_filters.CharFilter(lookup_expr="icontains")
    fcc_file_num = django_filters.CharFilter(lookup_expr="icontains")
    call_sign = django_filters.CharFilter(lookup_expr="icontains")
    meets_erpd_limit = django_filters.ChoiceFilter(
        label="Meets ERPd Limit",
        method="filter_meets_erpd_limit",
        choices=(("false", "False"), ("true", "True"), ("none", "None")),
    )
    sgrs_approval = django_filters.ChoiceFilter(
        label="SGRS Approval",
        method="filter_sgrs_approval",
        choices=(("false", "False"), ("true", "True"), ("none", "None")),
    )
    search = WatsonFilter(label="Search all text fields")
    num_sites = RangeNotationFilter(label="# Facilities Indicated")
    num_facilities = RangeNotationFilter(label="# Facilities Evaluated")
    si_done = django_filters.DateFromToRangeFilter(
        field_name="si_done", label="SI Done"
    )
    date_received = django_filters.DateFromToRangeFilter()
    # TODO: Broken...
    # case_groups = django_filters.ModelChoiceFilter(
    #     queryset=models.CaseGroup.objects.all(), widget=CaseGroupWidget()
    # )
    agency_num = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = models.Case
        formhelper_class = CaseFilterFormHelper
        fields = discover_fields(formhelper_class.layout)

    def filter_sgrs_approval(self, queryset, name, value):
        if value == "true":
            status = True
            return queryset.filter(sgrs_approval=status)
        elif value == "false":
            status = False
            return queryset.filter(sgrs_approval=status)
        elif value == "none":
            status = None
            return queryset.filter(sgrs_approval=status)
        else:
            return queryset

    def filter_meets_erpd_limit(self, queryset, name, value):
        if value == "true":
            status = True
            return queryset.filter(meets_erpd_limit=status)
        elif value == "false":
            status = False
            return queryset.filter(meets_erpd_limit=status)
        elif value == "none":
            status = None
            return queryset.filter(meets_erpd_limit=status)
        else:
            return queryset


class PersonFilter(HelpedFilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
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
    file_path = django_filters.CharFilter(lookup_expr="icontains")
    comments = django_filters.CharFilter(lookup_expr="search")
    hash_on_disk = django_filters.BooleanFilter(
        label="File Exists", method="filter_exists"
    )
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = models.Attachment
        formhelper_class = AttachmentFilterFormHelper
        fields = discover_fields(formhelper_class.layout)

    def filter_exists(self, queryset, name, value):
        return queryset.filter(hash_on_disk__isnull=not value)


class StructureFilter(HelpedFilterSet):
    location = PointFilter()

    class Meta:
        model = models.Structure
        formhelper_class = StructureFilterFormHelper
        fields = discover_fields(formhelper_class.layout)
