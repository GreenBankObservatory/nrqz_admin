"""Custom django_tables2.Table sub-classes for cases app"""

import django_tables2 as tables

from utils.coord_utils import lat_to_string, long_to_string, coords_to_string
from . import models
from .filters import (
    AttachmentFilter,
    PreliminaryFacilityFilter,
    FacilityFilter,
    PersonFilter,
    CaseFilter,
    StructureFilter,
    PreliminaryCaseFilter,
    PreliminaryCaseGroupFilter,
)
from .columns import SelectColumn, TrimmedTextColumn, UnboundFileColumn


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
        return coords_to_string(latitude=latitude, longitude=longitude, concise=True)


class PreliminaryFacilityTable(tables.Table):
    id = tables.Column(linkify=True)
    comments = TrimmedTextColumn()

    class Meta:
        model = models.PreliminaryFacility
        fields = ["id"] + PreliminaryFacilityFilter.Meta.fields

    # TODO: Consolidate!
    def render_location(self, value):
        """Render a coordinate as DD MM SS.sss"""
        longitude, latitude = value.coords
        return coords_to_string(latitude=latitude, longitude=longitude, concise=True)


class FacilityTable(tables.Table):
    nrqz_id = tables.Column(
        linkify=True, empty_values=(), order_by=["case__case_num", "-nrqz_id"]
    )
    # comments = TrimmedTextColumn()
    # structure = tables.Column(linkify=True)
    case = tables.Column(linkify=True)
    path = tables.Column(empty_values=())
    dominant_path = tables.Column(verbose_name="Dom. Path")
    calc_az = tables.Column(
        verbose_name="Az. Bearing to GBT", accessor="azimuth_to_gbt"
    )
    applicant = tables.Column(linkify=True, accessor="case.applicant")
    latitude = tables.Column(accessor="location", verbose_name="Latitude")
    longitude = tables.Column(accessor="location", verbose_name="Longitude")
    in_nrqz = tables.Column(empty_values=(), accessor="in_nrqz", verbose_name="In NRQZ")
    distance_to_gbt = tables.Column(
        empty_values=(), accessor="distance_to_gbt", verbose_name="Distance to GBT"
    )
    azimuth_to_gbt = tables.Column(
        empty_values=(),
        accessor="azimuth_to_gbt",
        verbose_name="Azimuth Bearing to GBT",
    )

    class Meta:
        model = models.Facility
        fields = [
            field
            for field in FacilityFilter.Meta.fields
            if field
            not in [
                "structure",
                "data_source",
                "site_num",
                "comments",
                "az_bearing",
                "contact",
                "location",
            ]
        ]
        order_by = ["-nrqz_id", "freq_low"]

    def render_path(self, record):
        fia = record.model_import_attempt.file_import_attempt
        if "stripped_data_only_" in fia.name:
            path = fia.name[len("stripped_data_only_") :].replace("_", " ")
        else:
            path = fia.name
        return path

    def render_nrao_aerpd(self, value):
        return f"{value:.2f}"

    def render_calc_az(self, value):
        return f"{value:.2f}°"

    def render_nrqz_id(self, record):
        return record.nrqz_id or record.case.case_num

    def render_case(self, value):
        return value.case_num

    # TODO: Consolidate!
    def render_latitude(self, value):
        return lat_to_string(latitude=value.y, concise=True)

    # TODO: Consolidate!
    def render_longitude(self, value):
        return lat_to_string(latitude=value.x, concise=True)

    def render_dominant_path(self, value):
        if value:
            return value[0]
        return value

    def render_in_nrqz(self, record):
        return record.in_nrqz

    def render_distance_to_gbt(self, record):
        if record.distance_to_gbt is not None:
            return f"{record.distance_to_gbt.mi:.2f} miles"
        return None

    def render_azimuth_to_gbt(self, record):
        if record.azimuth_to_gbt is not None:
            return f"{record.azimuth_to_gbt:.2f}°"
        return None


class FacilityExportTable(FacilityTable):
    class Meta:
        model = models.Facility
        exclude = [
            "model_import_attempt",
            "is_active",
            "original_created_on",
            "original_modfied_on",
            "created_on",
            "modified_on",
            "data-source",
            "id",
        ]
        order_by = ["-nrqz_id", "freq_low"]


class FacilityTableWithConcur(FacilityTable):
    selected = SelectColumn()

    class Meta:
        model = models.Facility
        fields = FacilityFilter.Meta.fields + ["selected"]


class PreliminaryCaseGroupTable(tables.Table):
    comments = TrimmedTextColumn()

    class Meta:
        model = models.PreliminaryCaseGroup
        fields = PreliminaryCaseGroupFilter.Meta.fields
        # order_by = ["-case_num"]

    # def render_case_num(self, value):
    #     return f"P{value}"


class PreliminaryCaseTable(tables.Table):
    case_num = tables.Column(linkify=True)
    applicant = tables.Column(linkify=True)
    contact = tables.Column(linkify=True)
    comments = TrimmedTextColumn()

    class Meta:
        model = models.PreliminaryCase
        fields = PreliminaryCaseFilter.Meta.fields
        order_by = ["-case_num"]

    def render_case_num(self, value):
        return f"P{value}"


class CaseTable(tables.Table):
    case_num = tables.Column(linkify=True)
    applicant = tables.Column(linkify=True)
    contact = tables.Column(linkify=True)
    comments = TrimmedTextColumn()

    nrao_approval = tables.Column(empty_values=())
    sgrs_approval = tables.Column(empty_values=())

    class Meta:
        model = models.Case
        fields = CaseFilter.Meta.fields
        order_by = ["-case_num"]

    def render_nrao_approval(self, record):
        return record.nrao_approval


class CaseExportTable(CaseTable):
    class Meta:
        model = models.Case
        # fields = CaseFilter.Meta.fields
        order_by = ["-case_num"]


class PersonTable(tables.Table):
    name = tables.Column(linkify=True)
    comments = TrimmedTextColumn()

    class Meta:
        model = models.Person
        fields = PersonFilter.Meta.fields


class AttachmentTable(tables.Table):
    path = tables.Column(linkify=True)
    file = UnboundFileColumn(accessor="path")

    class Meta:
        model = models.Attachment
        fields = AttachmentFilter.Meta.fields
        order_by = ["original_index"]


class StructureTable(tables.Table):
    asr = tables.Column(linkify=True)

    class Meta:
        model = models.Structure
        fields = StructureFilter.Meta.fields

    def render_location(self, value):
        """Render a coordinate as DD MM SS.sss"""
        longitude, latitude = value.coords
        return coords_to_string(latitude=latitude, longitude=longitude, concise=True)
