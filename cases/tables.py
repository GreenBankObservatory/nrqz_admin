from django.utils.safestring import mark_safe
from django.utils.html import escape

import django_tables2 as tables
from django_tables2.utils import AttributeDict

from utils.coord_utils import coords_to_string
from . import models
from .filters import (
    AttachmentFilter,
    BatchFilter,
    FacilityFilter,
    PersonFilter,
    CaseFilter,
)


class LetterFacilityTable(tables.Table):
    nrqz_id = tables.Column(verbose_name="NRQZ ID")
    site_name = tables.Column(verbose_name="Site Name")
    max_output = tables.Column(verbose_name="Max TX Power (W)")
    # antenna_gain = tables.Column(verbose_name="Max Gain (dBi)")
    antenna_model_number = tables.Column(verbose_name="Antenna Model")
    # = tables.Column(verbose_name="Calculated max ERPd per TX (W) prior to system loss")
    tx_per_sector = tables.Column(verbose_name="Num TX per sector")
    # = tables.Column(verbose_name="Num TX per facility")
    # latitude = tables.Column(verbose_name="Lat N (NAD83)")
    # longitude = tables.Column(verbose_name="Lon W (NAD83)")
    amsl = tables.Column(verbose_name="MSL (m)")
    agl = tables.Column(verbose_name="AGL (m)")
    freq_low = tables.Column(verbose_name="Freq Low (MHz)")
    freq_high = tables.Column(verbose_name="Freq High (MHz)")
    bandwidth = tables.Column(verbose_name="Bandwidth BW (MHz)")
    # = tables.Column(verbose_name="AZ° True")
    mechanical_downtilt = tables.Column(verbose_name="Mechanical-DT")
    electrical_downtilt = tables.Column(verbose_name="Electrical-DT")
    # = tables.Column(verbose_name="NRAO AERPd (W)")
    # = tables.Column(verbose_name="Max ERPd of Facility")
    class Meta:
        model = models.Facility
        fields = (
            "nrqz_id",
            "site_name",
            "max_output",
            "antenna_model_number",
            "tx_per_sector",
            "location",
            "amsl",
            "agl",
            "freq_low",
            "freq_high",
            "bandwidth",
            "mechanical_downtilt",
            "electrical_downtilt",
        )
        orderable = False

    def render_location(self, value):
        """Render a coordinate as DD MM SS.sss"""
        longitude, latitude = value.coords
        return coords_to_string(latitude=latitude, longitude=longitude)


class TrimmedTextColumn(tables.Column):
    def __init__(self, *args, length=80, **kwargs):
        super(TrimmedTextColumn, self).__init__(*args, **kwargs)
        self.trim_length = length

    def render(self, value):
        value = escape(value)
        first_line = value.split("\n")[0]
        if len(first_line) > self.trim_length:
            trimmed = " ".join(first_line[: self.trim_length].split(" ")[:-1])
            return mark_safe(f"<span title='{value[:512]}'>{trimmed} ...</span>")
        return first_line


class SelectColumn(tables.CheckBoxColumn):
    verbose_name = "Concur"
    empty_values = ()

    def __init__(self, *args, **kwargs):
        super(SelectColumn, self).__init__(*args, **kwargs)

    @property
    def header(self):
        return mark_safe(f"<span>{SelectColumn.verbose_name}</span>")

    def render(self, value, bound_column, record):
        attrs = AttributeDict(
            {"type": "checkbox", "name": "facilities", "value": record.id}
        )
        return mark_safe("<input %s/>" % attrs.as_html())


class FacilityTable(tables.Table):
    nrqz_id = tables.Column(linkify=True)
    selected = SelectColumn()
    comments = TrimmedTextColumn()

    class Meta:
        model = models.Facility
        fields = FacilityFilter.Meta.fields + ["selected"]

    def render_location(self, value):
        """Render a coordinate as DD MM SS.sss"""
        longitude, latitude = value.coords
        return coords_to_string(latitude=latitude, longitude=longitude)


class CaseTable(tables.Table):
    case_num = tables.Column(linkify=True)
    applicant = tables.Column(linkify=True)
    contact = tables.Column(linkify=True)
    comments = TrimmedTextColumn()

    class Meta:
        model = models.Case
        fields = CaseFilter.Meta.fields


class BatchTable(tables.Table):
    name = tables.Column(linkify=True)
    comments = TrimmedTextColumn()

    class Meta:
        model = models.Batch
        fields = BatchFilter.Meta.fields


class PersonTable(tables.Table):
    comments = TrimmedTextColumn()

    class Meta:
        model = models.Person
        fields = PersonFilter.Meta.fields


class AttachmentTable(tables.Table):
    path = tables.Column(linkify=True)
    comments = TrimmedTextColumn()

    class Meta:
        model = models.Attachment
        fields = AttachmentFilter.Meta.fields
