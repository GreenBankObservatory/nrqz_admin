"""Case models"""

import math
import ntpath
import os

from django.conf import settings
from django.contrib.gis.db.backends.postgis.models import PostGISSpatialRefSys
from django.contrib.gis.db.models import PointField, PolygonField
from django.contrib.gis.db.models.functions import Area, Azimuth, Distance
from django.contrib.postgres.fields import ArrayField
from django.db.models import (
    BooleanField,
    CASCADE,
    CharField,
    DateField,
    DateTimeField,
    EmailField,
    F,
    FilePathField,
    FloatField,
    ForeignKey,
    IntegerField,
    ManyToManyField,
    Model,
    PositiveIntegerField,
    PROTECT,
    SET_NULL,
    SlugField,
    TextField,
    Value,
)
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from django_import_data.models import AbstractBaseAuditedModel
from django_import_data.mixins import (
    SensibleCharField,
    SensibleEmailField,
    SensibleTextField,
    TrackedFileMixin,
)
from django_super_deduper.models import MergeInfo

from .kml import facility_as_kml, case_as_kml, kml_to_string
from .managers import (
    AttachmentManager,
    CaseManager,
    LocationManager,
    CaseGroupManager,
    PersonManager,
)
from .mixins import (
    AllFieldsModel,
    DataSourceModel,
    IsActiveModel,
    TrackedModel,
    TrackedOriginalModel,
    CaseGroupModel,
)
from utils.constants import WGS84_SRID
from utils.numrange import get_str_from_nums
from utils.misc import to_file_link

# TODO: Make proper field
LOCATION_FIELD = lambda: PointField(
    blank=True,
    null=True,
    # Creates a spatial index for the given geometry field.
    spatial_index=True,
    # Use geography column (spherical) instead of geometry (planar)
    geography=True,
    # WGS84_SRID
    srid=WGS84_SRID,
    help_text="A physical location on the Earth",
    verbose_name="Location",
)


def get_case_num():
    try:
        return Case.objects.order_by("case_num").last().case_num + 1
    except AttributeError:
        return 1


def get_pcase_num():
    try:
        return PreliminaryCase.objects.order_by("case_num").last().case_num + 1
    except AttributeError:
        return 1


class Boundaries(IsActiveModel, Model):
    name = SensibleCharField(
        max_length=64, default=None, unique=True, verbose_name="Name"
    )
    bounds = PolygonField(geography=True, srid=WGS84_SRID, verbose_name="Bounds")

    class Meta:
        verbose_name = "Boundaries"
        verbose_name_plural = "Boundaries"

    def __str__(self):
        return self.name

    @cached_property
    def area(self):
        return (
            Boundaries.objects.filter(id=self.id)
            .annotate(area=Area(F("bounds")))
            .values("area")
            .last()["area"]
        )


class Location(IsActiveModel, Model):
    name = SensibleCharField(
        max_length=64, default=None, unique=True, verbose_name="Name"
    )
    location = PointField(geography=True, srid=WGS84_SRID, verbose_name="Location")

    def __str__(self):
        return self.name


class Structure(IsActiveModel, TrackedModel, DataSourceModel, Model):
    """Represents a physical structure; modeled after FCC ASR DB"""

    asr = PositiveIntegerField(unique=True, verbose_name="ASR Num.", db_index=True)
    file_num = SensibleCharField(
        max_length=256, default=None, verbose_name="File Number"
    )
    location = LOCATION_FIELD()
    faa_circ_num = SensibleCharField(
        max_length=256, default=None, verbose_name="FAA Circulation Number"
    )
    faa_study_num = SensibleCharField(
        max_length=256, default=None, verbose_name="FAA Study Number"
    )
    issue_date = DateField(verbose_name="Issue Date")
    height = FloatField(verbose_name="Height (m)")

    def __str__(self):
        return str(self.asr)

    def get_absolute_url(self):
        return reverse("structure_detail", args=[str(self.id)])


class AbstractBaseFacility(
    AllFieldsModel,
    AbstractBaseAuditedModel,
    TrackedOriginalModel,
    IsActiveModel,
    TrackedModel,
    DataSourceModel,
    Model,
):
    """Stores concrete fields common between PFacility and Facility"""

    nrqz_id = SensibleCharField(
        max_length=256,
        blank=True,
        verbose_name="NRQZ ID",
        help_text="Assigned by NRAO. Do not put any of your data in this column.",
        db_index=True,
        default=None,
    )
    site_num = PositiveIntegerField(
        verbose_name="Site #", blank=True, null=True, help_text="???"
    )
    freq_low = FloatField(
        verbose_name="Freq Low (MHz)",
        null=True,
        blank=True,
        help_text="Frequency specific or lower part of band.",
    )
    freq_high = FloatField(
        verbose_name="Freq High (MHz)",
        help_text="Frequency specific or upper part of band.",
        blank=True,
        null=True,
    )
    antenna_model_number = SensibleCharField(
        verbose_name="Antenna Model No.",
        max_length=256,
        blank=True,
        help_text="Antenna Model Number",
    )
    power_density_limit = FloatField(
        null=True, blank=True, verbose_name="Power Density Limit"
    )
    site_name = SensibleCharField(
        max_length=256,
        blank=True,
        verbose_name="Site Name",
        help_text="What you call it! Include MCN and eNB information.",
    )
    latitude = SensibleCharField(
        blank=True,
        max_length=256,
        verbose_name="Latitude",
        help_text="Latitude of site, in degrees",
    )
    longitude = SensibleCharField(
        blank=True,
        max_length=256,
        verbose_name="Longitude",
        help_text="Longitude of site, in degrees",
    )
    location = LOCATION_FIELD()
    location_description = SensibleCharField(
        blank=True,
        max_length=512,
        verbose_name="Geographic Location",
        help_text="A long-form description of the facility location",
    )
    original_srs = ForeignKey(
        PostGISSpatialRefSys,
        on_delete=PROTECT,
        help_text="The spatial reference system of the original imported coordinates",
        verbose_name="Original Spatial Reference System",
        blank=True,
        null=True,
    )
    amsl = FloatField(
        verbose_name="AMSL (meters)",
        blank=True,
        null=True,
        help_text="Facility ground elevation, in meters",
    )
    agl = FloatField(
        verbose_name="AGL (meters)",
        blank=True,
        null=True,
        help_text="Facility height to center above ground level, in meters",
    )
    comments = SensibleTextField(
        blank=True,
        help_text="Additional information or comments from the applicant",
        verbose_name="Comments",
    )
    usgs_dataset = SensibleCharField(
        max_length=3,
        choices=(("3m", "3m"), ("10m", "10m"), ("30m", "30m")),
        blank=True,
        verbose_name="USGS Dataset",
    )
    tpa = FloatField(null=True, blank=True, verbose_name="TPA")
    survey_1a = BooleanField(null=True, blank=True, verbose_name="Survey 1A")
    survey_2c = BooleanField(null=True, blank=True, verbose_name="Survey 2C")
    radio_service = SensibleCharField(
        max_length=256, blank=True, verbose_name="Radio Service"
    )
    topo_4_point = BooleanField(null=True, blank=True, verbose_name="FCC 4 Point")
    topo_12_point = BooleanField(
        null=True, blank=True, verbose_name="Weighted 12 Point"
    )
    propagation_model = SensibleCharField(
        max_length=256,
        default="Rounded Obstacle",
        verbose_name="Propagation Model",
        blank=True,
    )
    nrao_aerpd_cdma = FloatField(null=True, blank=True)
    nrao_aerpd_cdma2000 = FloatField(null=True, blank=True)
    nrao_aerpd_gsm = FloatField(null=True, blank=True)
    nrao_aerpd_analog = FloatField(null=True, blank=True)
    nrao_diff = FloatField(null=True, blank=True)
    nrao_space = FloatField(null=True, blank=True)
    nrao_tropo = FloatField(null=True, blank=True)
    original_outside_nrqz = BooleanField(null=True, blank=True)
    requested_max_erp_per_tx = SensibleCharField(
        max_length=256, blank=True, verbose_name="Max ERPd per TX"
    )
    az_bearing = SensibleCharField(
        max_length=256,
        blank=True,
        verbose_name="AZ bearing degrees True",
        help_text="The Azimuth bearing between the Facility and the GBT, as imported from existing data",
    )

    class Meta:
        abstract = True

    # @cached_property
    def get_distance_to_gbt(self):
        if self.location is None:
            return None
        return (
            Location.objects.filter(name="GBT")
            .annotate(distance=Distance(F("location"), self.location))
            .values("distance")
            .last()["distance"]
        )

    # @cached_property
    def get_azimuth_to_gbt(self):
        if self.location is None:
            return None
        return math.degrees(
            Location.objects.filter(name="GBT")
            .annotate(azimuth=Azimuth(F("location"), self.location))
            .values("azimuth")
            .last()["azimuth"]
        )

    # @cached_property
    def get_in_nrqz(self):
        if self.location is None:
            return None
        return Boundaries.objects.filter(
            name="NRQZ", bounds__covers=self.location
        ).exists()

    def get_prop_study_as_link(self, text=None):
        if not self.propagation_study:
            return None

        return self.propagation_study.hyperlink

    objects = LocationManager()


class PreliminaryFacility(AbstractBaseFacility):
    """A "Preliminary" Facility: a Facility that does not yet exist"""

    pcase = ForeignKey(
        "PreliminaryCase",
        on_delete=CASCADE,
        related_name="pfacilities",
        help_text="The Preliminary Case that this Facility is being considered under",
    )

    attachments = ManyToManyField(
        "Attachment", related_name="prelim_facilities", blank=True
    )
    propagation_study = ForeignKey(
        "Attachment",
        related_name="propagation_study_for_pfacilities",
        on_delete=CASCADE,
        null=True,
        blank=True,
        # limit_choices_to={"facilities__contains"}
    )

    objects = LocationManager()

    class Meta:
        verbose_name = "Preliminary Facility"
        verbose_name_plural = "Preliminary Facilities"

    def __str__(self):
        return f"{self.nrqz_id}"

    def get_absolute_url(self):
        return reverse("prelim_facility_detail", args=[str(self.id)])


class Facility(AbstractBaseFacility):
    """Describes a single, physical antenna"""

    site_name = SensibleCharField(
        max_length=256,
        blank=True,
        verbose_name="Site Name",
        help_text="What you call it! Include MCN and eNB information.",
    )
    call_sign = SensibleCharField(
        max_length=256,
        blank=True,
        verbose_name="Call Sign",
        help_text="The radio call sign of the Facility",
    )
    fcc_file_number = SensibleCharField(
        max_length=256, blank=True, verbose_name="FCC ULS Number", help_text="???"
    )

    bandwidth = FloatField(
        verbose_name="Bandwidth (MHz)",
        help_text="Minimum utilized per TX (i.e. 11K0F0E is a value of 0.011)",
        blank=True,
        null=True,
    )
    antenna_gain = FloatField(verbose_name="Antenna Gain (dBi)", blank=True, null=True)
    system_loss = FloatField(verbose_name="System Loss (dB)", blank=True, null=True)
    main_beam_orientation = SensibleCharField(
        max_length=256,
        verbose_name="Main Beam Orientation",
        help_text="or sectorized AZ bearings (in ° True NOT ° Magnetic)",
        blank=True,
    )
    mechanical_downtilt = SensibleCharField(
        verbose_name="Mechanical Downtilt", max_length=256, blank=True
    )
    electrical_downtilt = SensibleCharField(
        verbose_name="Electrical Downtilt",
        max_length=256,
        blank=True,
        help_text="Specific and/or RET range",
    )
    tx_per_sector = SensibleCharField(
        max_length=256,
        blank=True,
        verbose_name="Total number of TXers per sector",
        help_text="(or No. of RRH's ports with feed power",
    )
    case = ForeignKey("Case", on_delete=CASCADE, related_name="facilities")
    structure = ForeignKey(
        "Structure", blank=True, null=True, on_delete=CASCADE, related_name="facilities"
    )

    # From Working Data
    band_allowance = FloatField(null=True, blank=True, verbose_name="Band Allowance")
    distance_to_first_obstacle = SensibleCharField(
        max_length=256, blank=True, verbose_name="Distance to First Obstacle"
    )
    dominant_path = SensibleCharField(
        max_length=256,
        blank=True,
        verbose_name="Dominant Path",
        choices=(
            ("diffraction", "Diffraction"),
            ("scatter", "Scatter"),
            ("free_space", "Free Space"),
        ),
    )

    height_of_first_obstacle = FloatField(
        null=True, blank=True, verbose_name="Height of First Obstacle (ft)"
    )
    max_aerpd = FloatField(null=True, blank=True, verbose_name="Max AERPd (dBm)")
    max_eirp = FloatField(null=True, blank=True, verbose_name="Max AEiRP")
    requested_max_erp_per_tx = FloatField(
        null=True, blank=True, verbose_name="Max ERP per TX (W)"
    )
    max_gain = FloatField(null=True, blank=True, verbose_name="Max Gain (dBi)")
    max_tx_power = FloatField(null=True, blank=True, verbose_name="Max TX Pwr (W)")
    nrao_aerpd = FloatField(null=True, blank=True, verbose_name="NRAO AERPd (W)")
    power_density_limit = FloatField(
        null=True, blank=True, verbose_name="Power Density Limit"
    )
    sgrs_approval = BooleanField(null=True, blank=True, verbose_name="SGRS Approval")
    sgrs_responded_on = DateTimeField(
        null=True, blank=True, verbose_name="SGRS Responded On"
    )
    tap_file = SensibleCharField(max_length=256, blank=True)
    tx_power = FloatField(null=True, blank=True, verbose_name="TX Power (dBm)")
    aeirp_to_gbt = FloatField(null=True, blank=True, verbose_name="AEiRP to GBT")
    propagation_study = ForeignKey(
        "Attachment",
        related_name="propagation_study_for_facilities",
        on_delete=CASCADE,
        null=True,
        blank=True,
    )
    si_done = DateField(null=True, blank=True, verbose_name="SI Done")

    # calc_az = FloatField(
    #     verbose_name="Calculated Azimuth Bearing (°)",
    #     null=True,
    #     blank=True,
    #     help_text=(
    #         "Azimuth bearing between the Facility and the GBT, "
    #         "as calculated based on this Facility's, location"
    #     ),
    # )
    num_tx_per_facility = IntegerField(
        null=True, blank=True, verbose_name="# of TX per facility"
    )

    meets_erpd_limit = BooleanField(
        null=True,
        blank=True,
        help_text="Indicates whether NRAO approves of this Facility or not",
        verbose_name="Meets NRAO ERPd Limit",
    )

    attachments = ManyToManyField("Attachment", related_name="facilities", blank=True)

    emissions = ArrayField(SensibleCharField(max_length=64), null=True, blank=True)
    s367 = BooleanField(default=False)

    class Meta:
        verbose_name = "Facility"
        verbose_name_plural = "Facilities"

    def __iter__(self):
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    def __str__(self):
        if self.nrqz_id:
            nrqz_id_str = self.nrqz_id
        else:
            nrqz_id_str = "Facility"

        return f"{nrqz_id_str}"

    def get_absolute_url(self):
        return reverse("facility_detail", args=[str(self.id)])

    def as_kml(self):
        return kml_to_string(facility_as_kml(self))


class CaseGroup(TrackedModel, Model):
    """Provides a way to group groups of PreliminaryCases and Cases"""

    name = SensibleCharField(max_length=256, blank=True)
    comments = SensibleTextField(blank=True)
    cases = ManyToManyField("Case", related_name="case_groups", blank=True)
    pcases = ManyToManyField("PreliminaryCase", related_name="case_groups", blank=True)

    objects = CaseGroupManager()

    def get_absolute_url(self):
        return reverse("case_group_detail", args=[str(self.id)])

    def get_pcase_nums_as_ranges(self):
        return get_str_from_nums(
            self.pcases.values_list("case_num", flat=True), join_str=", ", prefix="P"
        )

    def get_case_nums_as_ranges(self):
        return get_str_from_nums(
            self.cases.values_list("case_num", flat=True), join_str=", "
        )

    def get_all_case_nums_as_ranges(self):
        case_nums_as_ranges = self.get_case_nums_as_ranges()
        pcase_nums_as_ranges = self.get_pcase_nums_as_ranges()

        return f"Cases: {case_nums_as_ranges}\nPrelim. Cases: {pcase_nums_as_ranges}"

    def __str__(self):

        if self.name:
            return self.name

        return super().__str__()

    def get_completed(self):
        return not self.cases.filter(completed=False).exists()


class AbstractBaseCase(
    CaseGroupModel,
    AllFieldsModel,
    AbstractBaseAuditedModel,
    TrackedOriginalModel,
    IsActiveModel,
    TrackedModel,
    DataSourceModel,
    Model,
):

    comments = SensibleTextField(blank=True)
    completed = BooleanField(default=False, blank=True, verbose_name="Completed")
    completed_on = DateTimeField(null=True, blank=True, verbose_name="Completed On")
    is_federal = BooleanField(null=True, verbose_name="Gov.", help_text="Gov.")
    num_freqs = PositiveIntegerField(null=True, blank=True, verbose_name="Num. Freq.")
    num_sites = PositiveIntegerField(
        null=True, blank=True, verbose_name="Num. Facilities"
    )
    radio_service = SensibleCharField(
        max_length=256, blank=True, verbose_name="Radio Service"
    )
    date_recorded = DateTimeField(null=True, blank=True, verbose_name="Date Recorded")

    slug = SlugField(unique=True)

    class Meta:
        abstract = True


class PreliminaryCase(AbstractBaseCase):
    applicant = ForeignKey(
        "Person",
        on_delete=CASCADE,
        related_name="applicant_for_prelim_cases",
        null=True,
        blank=True,
    )
    contact = ForeignKey(
        "Person",
        on_delete=CASCADE,
        related_name="contact_for_prelim_cases",
        null=True,
        blank=True,
    )
    case_num = PositiveIntegerField(
        unique=True,
        db_index=True,
        verbose_name="Prelim. Case Num.",
        default=get_pcase_num,
    )

    # case = ForeignKey(
    #     "Case", related_name="prelim_cases", on_delete=CASCADE, null=True, blank=True
    # )

    attachments = ManyToManyField("Attachment", related_name="prelim_cases", blank=True)

    objects = CaseManager()

    def __str__(self):
        return f"P{self.case_num}"

    def get_absolute_url(self):
        return reverse("prelim_case_detail", args=[str(self.case_num)])

    def save(self, *args, **kwargs):
        self.slug = str(self.case_num)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Preliminary Case"
        verbose_name_plural = "Preliminary Cases"


class Case(AbstractBaseCase):
    """Defines a given NRQZ Application"""

    applicant = ForeignKey(
        "Person",
        on_delete=CASCADE,
        related_name="applicant_for_cases",
        null=True,
        blank=True,
    )
    contact = ForeignKey(
        "Person",
        on_delete=CASCADE,
        related_name="contact_for_cases",
        null=True,
        blank=True,
    )
    case_num = PositiveIntegerField(
        unique=True, db_index=True, verbose_name="Case Num.", default=get_case_num
    )

    attachments = ManyToManyField("Attachment", related_name="cases", blank=True)

    # From Access
    shutdown = BooleanField(default=False, blank=True, verbose_name="Shut Down")
    sgrs_notify = BooleanField(default=False, blank=True, verbose_name="SGRS Notified")
    sgrs_responded_on = DateTimeField(
        null=True, blank=True, verbose_name="SGRS Responded On"
    )
    # TODO: Propagate to Facility
    call_sign = SensibleCharField(max_length=256, blank=True, verbose_name="Call Sign")
    freq_coord = SensibleCharField(
        max_length=256, blank=True, verbose_name="Freq. Coord. Num."
    )
    fcc_file_num = SensibleCharField(
        max_length=256, blank=True, verbose_name="FCC ULS Num."
    )
    num_outside = PositiveIntegerField(
        null=True, blank=True, verbose_name="Num. Sites Outside NRQZ"
    )
    original_meets_erpd_limit = BooleanField(
        default=False, blank=True, verbose_name="Original ERPd Limit"
    )
    si_waived = BooleanField(default=False, blank=True, verbose_name="SI Waived")
    si = BooleanField(default=False, blank=True, verbose_name="SI Req.")
    original_si_done = DateField(null=True, blank=True, verbose_name="SI Done")

    sgrs_service_num = SensibleCharField(
        max_length=256,
        blank=True,
        help_text="SGRS Service Num.",
        verbose_name="SGRS Service #",
    )
    agency_num = SensibleCharField(max_length=256, blank=True, help_text="Agency Num.")

    objects = CaseManager()

    class Meta:
        verbose_name = "Case"
        verbose_name_plural = "Cases"

    def __str__(self):
        return f"{self.case_num}"

    def get_absolute_url(self):
        return reverse("case_detail", args=[str(self.case_num)])

    def as_kml(self):
        return kml_to_string(case_as_kml(self))

    def save(self, *args, **kwargs):
        self.slug = str(self.case_num)
        super(Case, self).save(*args, **kwargs)

    def get_meets_erpd_limit(self):
        approvals = self.facilities.values("meets_erpd_limit").distinct()
        if not approvals.exists() or approvals.filter(meets_erpd_limit=None).exists():
            return None
        if approvals.filter(meets_erpd_limit=False).exists():
            return False

        return True

    def get_sgrs_approval(self):
        """Return the overall SGRS Approval status of this case

        If any Facilities have not yet been approved/denied, return None,
        indicating pending

        If any have been denied, return False, indicating denied

        Otherwise return True. This indicates that all Facilities have been
        approved by SGRS"""

        approvals = self.facilities.values("sgrs_approval").distinct()
        if not approvals.exists() or approvals.filter(sgrs_approval=None).exists():
            return None
        if approvals.filter(sgrs_approval=False).exists():
            return False

        return True

    def get_si_done(self):
        """Return the overall SGRS Approval status of this case

        If any Facilities have not yet been approved/denied, return None,
        indicating pending

        If any have been denied, return False, indicating denied

        Otherwise return True. This indicates that all Facilities have been
        approved by SGRS"""

        site_inspection_dates = self.facilities.values("si_done").distinct()
        if (
            not site_inspection_dates.exists()
            or site_inspection_dates.filter(si_done=None).exists()
        ):
            return None
        if site_inspection_dates.filter(si_done=False).exists():
            return False

        return True


class Person(
    AbstractBaseAuditedModel, IsActiveModel, TrackedModel, DataSourceModel, Model
):
    """A single, physical person"""

    name = SensibleCharField(max_length=256)
    phone = SensibleCharField(max_length=256, blank=True)
    fax = SensibleCharField(max_length=256, blank=True)
    email = SensibleEmailField(blank=True)
    street = SensibleCharField(max_length=256, blank=True)
    city = SensibleCharField(max_length=256, blank=True)
    county = SensibleCharField(max_length=256, blank=True)
    state = SensibleCharField(max_length=256, blank=True)
    zipcode = SensibleCharField(max_length=256, blank=True)
    comments = SensibleTextField(blank=True)
    merge_info = ForeignKey(MergeInfo, null=True, blank=True, on_delete=CASCADE)

    objects = PersonManager()

    def __str__(self):
        return f"{self.name}"

    def get_absolute_url(self):
        return reverse("person_detail", args=[str(self.id)])

    def natural_key(self):
        # print("THIS IS A HACK; IF YOU ARE SEEING THIS IT IS BAD")
        ret = (self.name, self.email)
        # print(f"Returning {ret}")
        return ret

    class Meta:
        verbose_name = "Person"
        verbose_name_plural = "People"


class Attachment(
    TrackedFileMixin,
    AbstractBaseAuditedModel,
    IsActiveModel,
    TrackedModel,
    DataSourceModel,
    Model,
):
    """Holds the path to a file along with some metadata"""

    comments = SensibleTextField(blank=True)
    original_index = PositiveIntegerField(null=True, blank=True)

    objects = AttachmentManager()

    class Meta:
        verbose_name = "Attachment"
        verbose_name_plural = "Attachments"

    def __str__(self):
        return f"{self.file_path}"

    def get_absolute_url(self):
        return reverse("attachment_detail", args=[str(self.id)])

    @cached_property
    def hyperlink(self):
        if self.file_path.startswith("http"):
            href = self.file_path
            path = self.file_path
        else:
            href = f"{to_file_link(self.file_path)}"
            nt_path = ntpath.basename(self.file_path)
            unix_path = os.path.basename(self.file_path)
            path = unix_path if len(unix_path) < len(nt_path) else nt_path

        link = f"<a href='{href}' " f"title={self.file_path}>" f"{path}</a>"
        return mark_safe(link)

    def get_is_active(self):
        self.is_active = os.path.isfile(self.file_path)
        self.save()
        return self.is_active

    def save(self, *args, **kwargs):
        if (
            self.file_path.startswith("'")
            or self.file_path.startswith('"')
            and self.file_path.endswith("'")
            or self.file_path.endswith('"')
        ):
            self.file_path = self.file_path[1:-1]

        super().save(*args, **kwargs)


class LetterTemplate(IsActiveModel, TrackedModel, Model):
    name = SensibleCharField(max_length=256, unique=True)
    path = FilePathField(
        path=settings.NRQZ_LETTER_TEMPLATE_DIR,
        max_length=512,
        unique=True,
        help_text=f"Save new files into '{settings.NRQZ_LETTER_TEMPLATE_DIR}' in order to select them here",
    )
    description = SensibleTextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Letter Template"
        verbose_name_plural = "Letter Templates"
