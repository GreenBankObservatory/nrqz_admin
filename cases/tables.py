import django_tables2 as tables

from utils.coord_utils import coords_to_string, dd_to_dms
from . import models
from .filters import (
    AttachmentFilter,
    BatchFilter,
    FacilityFilter,
    PersonFilter,
    CaseFilter,
)


class ConcurrenceFacilityTable(tables.Table):
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
