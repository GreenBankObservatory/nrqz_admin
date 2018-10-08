import django_tables2 as tables
from .filters import FacilityFilter
from . import models

class FacilityTable(tables.Table):
    site_name = tables.Column(linkify=True)
    class Meta:
        model = models.Facility
        fields = FacilityFilter.Meta.fields
