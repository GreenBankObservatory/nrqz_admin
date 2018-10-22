import django_tables2 as tables

from utils.coord_utils import coords_to_string, dd_to_dms
from . import models
from .filters import AttachmentFilter, BatchFilter, FacilityFilter, PersonFilter, CaseFilter


class FacilityTable(tables.Table):
    nrqz_id = tables.LinkColumn()

    class Meta:
        model = models.Facility
        fields = FacilityFilter.Meta.fields

    def render_location(self, value):
        """Render a coordinate as DD MM SS.sss"""
        longitude, latitude = value.coords
        return coords_to_string(latitude=latitude, longitude=longitude)


class CaseTable(tables.Table):
    case_num = tables.LinkColumn()
    batch = tables.LinkColumn()
    applicant = tables.LinkColumn()
    contact = tables.LinkColumn()

    class Meta:
        model = models.Case
        fields = CaseFilter.Meta.fields


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
