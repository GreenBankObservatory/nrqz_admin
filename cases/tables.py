"""Custom django_tables2.Table sub-classes for cases app"""
from django.utils.safestring import mark_safe

import django_tables2 as tables
from watson.models import SearchEntry

from audits.columns import TitledCheckBoxColumn
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
    CaseGroupFilter,
)
from .columns import SelectColumn, TrimmedTextColumn, UnboundFileColumn


class LetterFacilityTable(tables.Table):
    nrqz_id = tables.Column(verbose_name="Facility ID")
    site_name = tables.Column(verbose_name="Site Name")
    max_output = tables.Column(verbose_name="Max TX Power (W)")
    antenna_model_number = tables.Column(verbose_name="Antenna Model")
    tx_per_sector = tables.Column(verbose_name="Num TX per sector")
    amsl = tables.Column(verbose_name="MSL (m)")
    agl = tables.Column(verbose_name="AGL (m)")
    freq_low = tables.Column(verbose_name="Freq Low (MHz)")
    freq_high = tables.Column(verbose_name="Freq High (MHz)")
    bandwidth = tables.Column(verbose_name="Bandwidth BW (MHz)")
    mechanical_downtilt = tables.Column(verbose_name="Mechanical-DT")
    electrical_downtilt = tables.Column(verbose_name="Electrical-DT")

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


class BaseFacilityTable(tables.Table):
    # comments = TrimmedTextColumn()
    distance_to_gbt = tables.Column(
        empty_values=(), accessor="distance_to_gbt", verbose_name="Distance to GBT"
    )
    azimuth_to_gbt = tables.Column(
        empty_values=(),
        accessor="azimuth_to_gbt",
        verbose_name="Azimuth Bearing to GBT",
    )

    # in_nrqz = tables.Column(verbose_name="In NRQZ")
    # TODO: Consolidate!
    def render_latitude(self, value):
        return mark_safe(
            f"<span style='white-space:nowrap'>{lat_to_string(latitude=value.y, concise=True)}</span>"
        )

    # TODO: Consolidate!
    def render_longitude(self, value):
        return mark_safe(
            f"<span style='white-space:nowrap'>{long_to_string(longitude=value.x, concise=True)}</span>"
        )

    def value_latitude(self, value):
        return lat_to_string(latitude=value.y, concise=True)

    def value_longitude(self, value):
        return long_to_string(longitude=value.x, concise=True)

    def render_location(self, value):
        """Render a coordinate as DD MM SS.sss"""
        longitude, latitude = value.coords
        return coords_to_string(latitude=latitude, longitude=longitude, concise=True)

    def render_nrqz_id(self, record):
        return record.nrqz_id or record.case.case_num

    def render_in_nrqz(self, record):
        in_nrqz = getattr(record, "in_nrqz", None)
        if in_nrqz is None:
            in_nrqz = record.get_in_nrqz()
        return in_nrqz

    def render_distance_to_gbt(self, record):
        distance_to_gbt = getattr(record, "distance_to_gbt", None)
        if distance_to_gbt is None:
            distance_to_gbt = record.get_distance_to_gbt()
        if distance_to_gbt is None:
            return "—"
        return f"{distance_to_gbt.km:.2f} km"

    def render_azimuth_to_gbt(self, record):
        azimuth_to_gbt = getattr(record, "azimuth_to_gbt", None)
        if azimuth_to_gbt is None:
            azimuth_to_gbt = record.get_azimuth_to_gbt()
        if azimuth_to_gbt is None:
            return "—"
        return f"{azimuth_to_gbt:.2f}°"


class PreliminaryFacilityTable(BaseFacilityTable):
    nrqz_id = tables.Column(linkify=True, verbose_name="PFacility ID")
    pcase = tables.Column(
        linkify=True, verbose_name="PCase", order_by=["pcase__case_num"]
    )

    class Meta:
        model = models.PreliminaryFacility
        fields = PreliminaryFacilityFilter.Meta.fields
        order_by = ["-pcase", "site_num", "freq_low"]


class PreliminaryFacilityExportTable(PreliminaryFacilityTable):
    class Meta:
        model = models.PreliminaryFacility
        exclude = [
            "model_import_attempt",
            "is_active",
            "original_created_on",
            "original_modified_on",
            "created_on",
            "modified_on",
            "data_source",
            "id",
        ]
        order_by = ["-nrqz_id", "freq_low"]


class FacilityTable(BaseFacilityTable):
    nrqz_id = tables.Column(
        linkify=True,
        empty_values=(),
        order_by=["case__case_num", "-nrqz_id"],
        verbose_name="Facility ID",
    )
    case = tables.Column(linkify=True, order_by=["case__case_num", "nrqz_id"])
    # applicant = tables.Column(linkify=True, accessor="case.applicant")
    latitude = tables.Column(accessor="location", verbose_name="Latitude")
    longitude = tables.Column(accessor="location", verbose_name="Longitude")

    class Meta:
        model = models.Facility
        fields = [
            "nrqz_id",
            "case",
            "site_name",
            "latitude",
            "longitude",
            "freq_low",
            "freq_high",
            "main_beam_orientation",
            "distance_to_gbt",
            "azimuth_to_gbt",
            "nrao_aerpd",
            "requested_max_erp_per_tx",
            "si_done",
        ]
        order_by = ["-nrqz_id", "freq_low"]

    def render_requested_max_erp_per_tx(self, value):
        return f"{value:.2f}"

    def render_path(self, record):
        return record.model_import_attempt.file_import_attempt.name

    def render_nrao_aerpd(self, value):
        return f"{value:.2E}"

    def render_dominant_path(self, value):
        if value:
            return value[0]
        return value


class FacilityExportTable(FacilityTable):
    class Meta:
        model = models.Facility
        exclude = [
            "model_import_attempt",
            "is_active",
            "original_created_on",
            "original_modified_on",
            "created_on",
            "modified_on",
            "data_source",
            "id",
            "original_srs",
            "structure",
        ]
        order_by = ["-nrqz_id", "freq_low"]


class FacilityTableWithConcur(FacilityTable):
    selected = SelectColumn()

    class Meta:
        model = models.Facility
        fields = FacilityFilter.Meta.fields + ["selected"]


class CaseGroupTable(tables.Table):
    id = tables.Column(verbose_name="CG ID", linkify=True)
    comments = TrimmedTextColumn()
    num_cases = tables.Column(verbose_name="# Cases")
    num_pcases = tables.Column(verbose_name="# Prelim. Cases")

    completed = tables.BooleanColumn(
        attrs={
            "th": {
                "title": "A Case Group is completed once all of its Cases are "
                "completed. Prelim. Cases ARE NOT considered."
            }
        }
    )

    class Meta:
        model = models.CaseGroup
        fields = CaseGroupFilter.Meta.fields

    def render_id(self, record):
        if record.name:
            return f"{record.name} (CG {record.id})"

        return f"CG {record.id}"


class BaseCaseTable(tables.Table):
    case_num = tables.Column(linkify=True)
    applicant = tables.Column(linkify=True)
    contact = tables.Column(linkify=True)
    # comments = TrimmedTextColumn()


class PreliminaryCaseTable(BaseCaseTable):
    class Meta:
        model = models.PreliminaryCase
        fields = PreliminaryCaseFilter.Meta.fields
        order_by = ["-case_num"]

    def render_case_num(self, value):
        return f"P{value}"


class PreliminaryCaseExportTable(PreliminaryCaseTable):
    class Meta:
        model = models.PreliminaryCase
        exclude = [
            "model_import_attempt",
            "is_active",
            "original_created_on",
            "original_modified_on",
            "created_on",
            "modified_on",
            "data_source",
            "id",
        ]
        order_by = ["-case_num"]


class CaseTable(BaseCaseTable):
    meets_erpd_limit = tables.BooleanColumn(accessor="meets_erpd_limit", null=True)
    sgrs_approval = tables.BooleanColumn(
        accessor="sgrs_approval", null=True, verbose_name="SGRS Approval"
    )
    num_facilities = tables.Column(verbose_name="# Facilities")
    si_done = tables.Column(
        verbose_name="SI Done",
        attrs={"th": {"title": "The date of the most recent site inspection (if any)"}},
    )
    date_recorded = tables.DateColumn()

    class Meta:
        model = models.Case
        fields = CaseFilter.Meta.fields
        exclude = ("search",)
        order_by = ["-case_num"]


class CaseExportTable(CaseTable):
    class Meta:
        model = models.Case
        exclude = [
            "model_import_attempt",
            "is_active",
            "original_created_on",
            "original_modified_on",
            "created_on",
            "modified_on",
            "data_source",
            "id",
        ]
        order_by = ["-case_num"]


class PersonTable(tables.Table):
    name = tables.Column(linkify=True)
    comments = TrimmedTextColumn()

    class Meta:
        model = models.Person
        fields = PersonFilter.Meta.fields
        exclude = ("search",)


class AttachmentTable(tables.Table):
    file_path = tables.Column(linkify=True, verbose_name="Attachment")
    file = UnboundFileColumn(accessor="file_path", verbose_name="Link")
    original_index = tables.Column(verbose_name="Letter #")

    class Meta:
        model = models.Attachment
        fields = AttachmentFilter.Meta.fields
        exclude = ("is_active", "hash_on_disk")
        order_by = ["-modified_on", "original_index"]


class AttachmentDashboardTable(AttachmentTable):
    check = TitledCheckBoxColumn(
        accessor="id",
        attrs={
            "th": {
                "title": "Select the Attachments you want to affect (or the checkbox here to affect all of them)"
            },
            "th__input": {"title": "Select all", "name": "all"},
        },
        verbose_name="Select",
    )

    class Meta:
        model = models.Attachment
        fields = AttachmentFilter.Meta.fields
        exclude = ("is_active", "hash_on_disk", "file")
        order_by = ["-modified_on", "original_index"]


class StructureTable(tables.Table):
    asr = tables.Column(linkify=True)
    num_cases = tables.Column(verbose_name="# Cases")
    num_facilities = tables.Column(verbose_name="# Facilities")

    class Meta:
        model = models.Structure
        fields = StructureFilter.Meta.fields

    def render_location(self, value):
        """Render a coordinate as DD MM SS.sss"""
        longitude, latitude = value.coords
        return coords_to_string(latitude=latitude, longitude=longitude, concise=True)


class SearchEntryTable(tables.Table):
    title = tables.Column(linkify=True)

    class Meta:
        model = SearchEntry
        fields = ("title", "content")

    def __init__(self, *args, **kwargs):
        if not hasattr(self, "query"):
            raise ValueError(
                "'SearchEntryTable.query' attribute must be set prior to instantiation!"
            )
        super().__init__(*args, **kwargs)

    def render_content(self, value, record):
        window_size = 60
        try:
            found_index = value.lower().index(self.query.lower())
        except ValueError:
            return value

        bold_value = (
            value[:found_index]
            + "<b>"
            + value[found_index : found_index + len(self.query)]
            + "</b>"
            + value[found_index + len(self.query) :]
        )
        start_index = 0 if found_index - window_size < 0 else found_index - window_size
        end_index = (
            None
            if found_index + window_size > len(bold_value)
            else found_index + window_size
        )
        substring = bold_value[start_index:end_index]
        return mark_safe(f"...{substring}...")
