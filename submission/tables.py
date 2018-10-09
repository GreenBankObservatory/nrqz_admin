import django_tables2 as tables
from .filters import FacilityFilter
from . import models

from utils.coord_utils import dd_to_dms


class FacilityTable(tables.Table):
    site_name = tables.Column(linkify=True)
    class Meta:
        model = models.Facility
        fields = FacilityFilter.Meta.fields

    def _render_coord(self, value):
        d, m, s = dd_to_dms(value)
        return f"{d:3d} {m:2d} {s:2.3f}"

    render_latitude = _render_coord
    render_longitude = _render_coord
