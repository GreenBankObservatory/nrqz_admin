import django_tables2 as tables

from utils.coord_utils import dd_to_dms
from . import models
from .filters import AttachmentFilter, BatchFilter, FacilityFilter, PersonFilter, SubmissionFilter


class FacilityTable(tables.Table):
    nrqz_id = tables.LinkColumn()

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
    case_num = tables.LinkColumn()
    batch = tables.LinkColumn()
    applicant = tables.LinkColumn()
    contact = tables.LinkColumn()

    class Meta:
        model = models.Submission
        fields = SubmissionFilter.Meta.fields


class BatchTable(tables.Table):
    name = tables.LinkColumn()

    class Meta:
        model = models.Batch
        fields = BatchFilter.Meta.fields


class PersonTable(tables.Table):
    class Meta:
        model = models.Person
        fields = PersonFilter.Meta.fields

class AttachmentTable(tables.Table):
    path = tables.LinkColumn()

    class Meta:
        model = models.Attachment
        fields = AttachmentFilter.Meta.fields
