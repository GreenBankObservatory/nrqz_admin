import django_tables2 as tables

from utils.coord_utils import dd_to_dms
from . import models
from .filters import FacilityFilter, SubmissionFilter


class FacilityTable(tables.Table):
    nrqz_id = tables.Column(linkify=True)

    class Meta:
        model = models.Facility
        fields = FacilityFilter.Meta.fields

    def _render_coord(self, value):
        """Render a coordinate as DD MM SS.sss"""

        d, m, s = dd_to_dms(value)
        return f"{d:3d} {m:2d} {s:2.3f}"

    render_latitude = _render_coord
    render_longitude = _render_coord


class SubmissionTable(tables.Table):
    name = tables.Column(linkify=True)

    class Meta:
        model = models.Submission
        fields = SubmissionFilter.Meta.fields
