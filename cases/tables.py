"""Custom django_tables2.Table sub-classes for cases app"""
from django.utils.safestring import mark_safe
from django.db.models import F

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
from .columns import (
    SelectColumn,
    TrimmedTextColumn,
    RemappedUnboundFileColumn,
    UnboundFileColumn,
)


class LetterCaseTable(tables.Table):
    is_approved_by_nrao = tables.Column(
        verbose_name="NRAO Approved", accessor="is_approved_by_nrao"
    )
    is_approved_by_sgrs = tables.Column(
        verbose_name="SGRS Approved", accessor="is_approved_by_sgrs"
    )

    class Meta:
        model = models.Facility
        orderable = False
        fields = (
            "case__case_num",
            "site_name",
            "location_description",
            "is_approved_by_nrao",
            "is_approved_by_sgrs",
        )


class LetterFacilityTable(tables.Table):
    nrqz_id = tables.Column(verbose_name="Facility ID")
    site_name = tables.Column(verbose_name="Site Name")
    max_tx_power = tables.Column(verbose_name="Max TX Power (W)")
    antenna_model_number = tables.Column(verbose_name="Antenna Model")
    amsl = tables.Column(verbose_name="MSL (m)")
    agl = tables.Column(verbose_name="AGL (m)")
    freq_low = tables.Column(verbose_name="Freq Low (MHz)")
    freq_high = tables.Column(verbose_name="Freq High (MHz)")
    bandwidth = tables.Column(verbose_name="Bandwidth BW (MHz)")
    mechanical_downtilt = tables.Column(verbose_name="Mechanical-DT")
    electrical_downtilt = tables.Column(verbose_name="Electrical-DT")
    latitude = tables.Column(accessor="location", verbose_name="Latitude")
    longitude = tables.Column(accessor="location", verbose_name="Longitude")

    def render_latitude(self, value):
        return lat_to_string(latitude=value.y, concise=True)

    def render_longitude(self, value):
        return long_to_string(longitude=value.x, concise=True)

    def render_requested_max_erp_per_tx(self, value):
        return f"{value:.1f}"

    def render_nrao_aerpd(self, value):
        # e.g. 2.0e+04
        return f"{value:.1e}"

    class Meta:
        model = models.Facility
        fields = (
            "nrqz_id",
            "site_name",
            "latitude",
            "longitude",
            "amsl",
            "max_tx_power",
            "tx_per_sector",
            "num_tx_per_facility",
            "freq_low",
            "freq_high",
            "bandwidth",
            "antenna_gain",
            "antenna_model_number",
            "agl",
            "az_bearing",
            "mechanical_downtilt",
            "electrical_downtilt",
            "requested_max_erp_per_tx",
            "nrao_aerpd",
        )
        orderable = False
        order_by = ["nrqz_id"]


class BaseFacilityTable(tables.Table):
    # comments = TrimmedTextColumn()
    distance_to_gbt = tables.Column(
        empty_values=(),
        accessor="distance_to_gbt",
        verbose_name="Dist. to GBT (km)",
        attrs={"th": {"title": "Distance to GBT (km)"}},
    )
    azimuth_to_gbt = tables.Column(
        empty_values=(),
        accessor="azimuth_to_gbt",
        verbose_name="Az. Bearing",
        attrs={"th": {"title": "Azimuth Bearing to GBT"}},
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
        return f"{azimuth_to_gbt:.3f}°"


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
    bandwidth = tables.Column(
        verbose_name="B/W (MHz)", attrs={"th": {"title": "Bandwidth (MHz)"}}
    )
    # file_path = UnboundFileColumn(
    #     accessor="model_import_attempt.model_importer.row_data.file_import_attempt.imported_from"
    # )

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
            "bandwidth",
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


class FacilityExportTable(tables.Table):
    applicant = tables.Column(accessor="case.applicant")
    latitude = tables.Column(accessor="location", verbose_name="Latitude")
    longitude = tables.Column(accessor="location", verbose_name="Longitude")
    az_bearing_derived = tables.Column(
        empty_values=(), verbose_name="Az. Bearing to GBT"
    )

    class Meta:
        model = models.Facility
        fields = [
            "applicant",
            # NRQZ ID
            "nrqz_id",
            # Site Name
            "site_name",
            # GeoLocation
            "location_description",
            # Call Sign
            "call_sign",
            # FCC File Number
            "fcc_file_num",
            # Lat N NAD83
            "latitude",
            # Lon NAD83
            "longitude",
            # MSL (m)
            "amsl",
            # Max TX Pwr (W)
            "max_tx_power",
            # No TX per sector
            "tx_per_sector",
            # No TX per facility
            "num_tx_per_facility",
            # Freq Low (MHz)
            "freq_low",
            # Freq High (MHz)
            "freq_high",
            # Bandwidth BW (MHz)
            "bandwidth",
            # Max Gain (dBi)
            "antenna_gain",
            # Antenna Model
            "antenna_model_number",
            # AGL (m)
            "agl",
            # AZ ° True
            "main_beam_orientation",
            # Mechanical-DT
            "mechanical_downtilt",
            # Electrical-DT
            "electrical_downtilt",
            # NRAO ERPd Limit (W)
            "nrao_aerpd",
            # ERP / # Tx
            "requested_max_erp_per_tx",
            "az_bearing_derived",
        ]
        order_by = ["nrqz_id", "freq_low"]

    def value_latitude(self, value):
        return lat_to_string(latitude=value.y, concise=True)

    def value_longitude(self, value):
        return long_to_string(longitude=value.x, concise=True)

    def value_az_bearing_derived(self, record):
        return record.get_azimuth_to_gbt()


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
        order_by = ["case_num"]


class CaseTable(BaseCaseTable):
    meets_erpd_limit = tables.BooleanColumn(accessor="meets_erpd_limit", null=True)
    sgrs_approval = tables.BooleanColumn(
        accessor="sgrs_approval", null=True, verbose_name="SGRS Approval"
    )
    num_sites = tables.Column(
        verbose_name="# Facilities Indicated",
        attrs={"th": {"title": "The number of Facilities there are SUPPOSED to be"}},
    )
    num_facilities = tables.Column(
        verbose_name="# Facilities Evaluated",
        attrs={
            "th": {"title": "The actual number of Facilities attached to this case"}
        },
    )
    date_received = tables.DateColumn()

    class Meta:
        model = models.Case
        fields = CaseFilter.Meta.fields
        exclude = ("search",)
        order_by = ["-date_received", "case_num"]

    def order_date_received(self, queryset, is_descending):
        order_attr = "desc" if is_descending else "asc"
        orderer = getattr(F("date_received"), order_attr)(nulls_last=True)
        queryset = queryset.order_by(
            orderer,
        )
        return (queryset, True)


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
        order_by = ["case_num"]


class PersonTable(tables.Table):
    name = tables.Column(linkify=True)
    comments = TrimmedTextColumn()

    class Meta:
        model = models.Person
        fields = PersonFilter.Meta.fields
        exclude = ("search",)


class AttachmentTable(tables.Table):
    file_path = tables.Column(linkify=True, verbose_name="Attachment")
    file = RemappedUnboundFileColumn(accessor="file_path", verbose_name="Link")
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
