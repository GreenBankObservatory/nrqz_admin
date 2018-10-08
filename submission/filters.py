import django_filters
from . import models

class FacilityFilter(django_filters.FilterSet):
    site_name = django_filters.CharFilter(lookup_expr='icontains')
    nrqz_id = django_filters.CharFilter(lookup_expr='icontains')
    call_sign = django_filters.CharFilter(lookup_expr='icontains')
    latitude = django_filters.CharFilter(lookup_expr='startswith')
    longitude = django_filters.CharFilter(lookup_expr='startswith')
    freq_low = django_filters.RangeFilter(lookup_expr='range')
    freq_high = django_filters.RangeFilter(lookup_expr='range')
    amsl = django_filters.RangeFilter(lookup_expr='range')
    agl = django_filters.RangeFilter(lookup_expr='range')

    class Meta:
        model = models.Facility
        fields = ("site_name", "nrqz_id", "latitude", "longitude", "amsl", "agl", "freq_low", "freq_high")

