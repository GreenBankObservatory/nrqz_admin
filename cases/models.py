import math

from django.conf import settings
from django.contrib.gis.db.backends.postgis.models import PostGISSpatialRefSys
from django.contrib.gis.db.models import PointField, PolygonField
from django.contrib.gis.db.models.functions import Area, Azimuth, Distance
from django.db.models import (
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    EmailField,
    FilePathField,
    FloatField,
    ForeignKey,
    IntegerField,
    ManyToManyField,
    Model,
    PositiveIntegerField,
    TextField,
    CASCADE,
    PROTECT,
    SET_NULL,
    SlugField,
    F,
)
from django.urls import reverse
from django.utils.functional import cached_property

from django_import_data.models import AbstractBaseAuditedModel

from utils.coord_utils import dd_to_dms
from .kml import facility_as_kml, case_as_kml, kml_to_string
from .mixins import DataSourceModel, TrackedOriginalModel, IsActiveModel, TrackedModel

LOCATION_FIELD = lambda: PointField(
    blank=True,
    null=True,
    # Creates a spatial index for the given geometry field.
    spatial_index=True,
    # Use geography column (spherical) instead of geometry (planar)
    geography=True,
    # WGS84
    srid=4326,
    help_text="A physical location on the Earth",
)


class Structure(IsActiveModel, TrackedModel, DataSourceModel, Model):
    """Represents a physical structure; modeled after FCC ASR DB"""

    asr = PositiveIntegerField(
        unique=True, verbose_name="Antenna Registration Number", db_index=True
    )
    file_num = CharField(max_length=256, verbose_name="File Number")
    location = LOCATION_FIELD()
    faa_circ_num = CharField(max_length=256, verbose_name="FAA Circulation Number")
    faa_study_num = CharField(max_length=256, verbose_name="FAA Study Number")
    issue_date = DateField(verbose_name="Issue Date")
    height = FloatField(verbose_name="Height (m)")
    # owner = ForeignKey("Person", on_delete=PROTECT, related_name="owner_for_structures")
    # contact = ForeignKey(
    #     "Person", on_delete=PROTECT, related_name="contact_for_structures"
    # )

    def __str__(self):
        return str(self.asr)

    def get_absolute_url(self):
        return reverse("structure_detail", args=[str(self.id)])


class AbstractBaseFacility(
    AbstractBaseAuditedModel,
    TrackedOriginalModel,
    IsActiveModel,
    TrackedModel,
    DataSourceModel,
    Model,
):
    """Stores concrete fields common between PFacility and Facility"""

    site_num = PositiveIntegerField(
        verbose_name="Site #", blank=True, null=True, help_text="???"
    )
    freq_low = FloatField(
        verbose_name="Freq Low (MHz)",
        null=True,
        blank=True,
        help_text="Frequency specific or lower part of band.",
    )
    antenna_model_number = CharField(
        verbose_name="Antenna Model No.",
        max_length=256,
        blank=True,
        null=True,
        help_text="Antenna Model Number",
    )
    power_density_limit = FloatField(
        null=True, blank=True, verbose_name="Power Density Limit", help_text="???"
    )
    site_name = CharField(
        max_length=256,
        blank=True,
        null=True,
        verbose_name="Site Name",
        help_text="What you call it! Include MCN and eNB information.",
    )
    latitude = CharField(
        blank=True,
        null=True,
        max_length=256,
        verbose_name="Latitude",
        help_text="Latitude of site, in degrees",
    )
    longitude = CharField(
        blank=True,
        null=True,
        max_length=256,
        verbose_name="Longitude",
        help_text="Longitude of site, in degrees",
    )
    location = LOCATION_FIELD()
    location_description = CharField(
        blank=True,
        null=True,
        max_length=512,
        verbose_name="Location Description",
        help_text="A long-form description of the facility location",
    )
    srid_used_for_import = ForeignKey(
        PostGISSpatialRefSys,
        on_delete=PROTECT,
        null=True,
        blank=True,
        help_text="The spatial reference system of the original imported coordinates",
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
    comments = TextField(
        null=True,
        blank=True,
        help_text="Additional information or comments from the applicant",
    )

    class Meta:
        abstract = True

    def distance_to_gbt(self):
        return (
            Location.objects.filter(name="GBT")
            .annotate(distance=Distance(F("location"), self.location))
            .values("distance")
            .last()["distance"]
        )

    def azimuth_to_gbt(self):
        return math.degrees(
            Location.objects.filter(name="GBT")
            .annotate(azimuth=Azimuth(F("location"), self.location))
            .values("azimuth")
            .last()["azimuth"]
        )


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

    class Meta:
        verbose_name = "Preliminary Facility"
        verbose_name_plural = "Preliminary Facilities"

    def __str__(self):
        return f"{self.antenna_model_number} <{self.id}>"

    def get_absolute_url(self):
        return reverse("prelim_facility_detail", args=[str(self.id)])


class Facility(AbstractBaseFacility):
    """Describes a single, physical antenna"""

    freq_low = FloatField(
        verbose_name="Freq Low (MHz)",
        null=True,
        blank=True,
        help_text="Frequency specific or lower part of band.",
    )
    site_name = CharField(
        max_length=256,
        blank=True,
        null=True,
        verbose_name="Site Name",
        help_text="What you call it! Include MCN and eNB information.",
    )
    call_sign = CharField(
        max_length=256,
        blank=True,
        null=True,
        verbose_name="Call Sign",
        help_text="The radio call sign of the Facility",
    )
    fcc_file_number = CharField(
        max_length=256,
        blank=True,
        null=True,
        verbose_name="FCC File Number",
        help_text="???",
    )
    freq_high = FloatField(
        verbose_name="Freq High (MHz)",
        help_text="Frequency specific or upper part of band.",
        blank=True,
        null=True,
    )
    bandwidth = FloatField(
        verbose_name="Bandwidth (MHz)",
        help_text="Minimum utilized per TX (i.e. 11K0F0E is a value of 0.011)",
        blank=True,
        null=True,
    )
    max_output = FloatField(
        verbose_name="Max Output Pwr (W)",
        help_text="Per Transmitter or RRH (remote radio head) polarization",
        blank=True,
        null=True,
    )
    antenna_gain = FloatField(verbose_name="Antenna Gain (dBi)", blank=True, null=True)
    system_loss = FloatField(verbose_name="System Loss (dB)", blank=True, null=True)
    main_beam_orientation = CharField(
        max_length=256,
        verbose_name="Main Beam Orientation",
        help_text="or sectorized AZ bearings (in ° True NOT ° Magnetic)",
        blank=True,
    )
    mechanical_downtilt = CharField(
        verbose_name="Mechanical Downtilt", max_length=256, blank=True, null=True
    )
    electrical_downtilt = CharField(
        verbose_name="Electrical Downtilt Sector",
        max_length=256,
        blank=True,
        help_text="Specific and/or RET range",
    )
    antenna_model_number = CharField(
        verbose_name="Antenna Model No.", max_length=256, blank=True, null=True
    )
    nrqz_id = CharField(
        max_length=256,
        blank=True,
        null=True,
        verbose_name="NRQZ ID",
        help_text="Assigned by NRAO. Do not put any of your data in this column.",
        db_index=True,
        # unique=True,
    )
    tx_per_sector = CharField(
        max_length=256,
        blank=True,
        verbose_name="Total number of TXers per sector",
        help_text="(or No. of RRH's ports with feed power",
    )
    tx_antennas_per_sector = CharField(
        max_length=256,
        blank=True,
        verbose_name="Number of transmitting antennas per sector",
    )
    technology = CharField(
        max_length=256,
        blank=True,
        null=True,
        help_text="i.e.  FM, 2G, 3G, 4G, GSM, LTE, UMTS, CDMA2000 (specify other)",
    )
    uses_split_sectorization = BooleanField(
        default=False,
        verbose_name="This facility uses split sectorization",
        help_text="or dual-beam sectorization",
        blank=True,
        null=True,
    )
    uses_cross_polarization = BooleanField(
        default=False,
        verbose_name="This facility uses Cross polarization ",
        blank=True,
        null=True,
    )
    uses_quad_or_octal_polarization = BooleanField(
        default=False,
        verbose_name="This facility uses Quad or Octal polarization",
        blank=True,
        null=True,
    )
    num_quad_or_octal_ports_with_feed_power = PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Number of Quad or Octal ports with feed power",
    )
    tx_power_pos_45 = FloatField(
        null=True, blank=True, verbose_name="Max TX output PWR at +45 degrees"
    )
    tx_power_neg_45 = FloatField(
        null=True, blank=True, verbose_name="Max TX output PWR at -45 degrees"
    )
    # TODO: Is this needed? Doesn't structure store this?
    asr_is_from_applicant = BooleanField(null=True, blank=True)

    case = ForeignKey("Case", on_delete=CASCADE, related_name="facilities")
    structure = ForeignKey(
        "Structure", blank=True, null=True, on_delete=CASCADE, related_name="facilities"
    )

    # From Working Data
    band_allowance = FloatField(null=True, blank=True, verbose_name="Band Allowance")
    distance_to_first_obstacle = CharField(
        max_length=256, null=True, blank=True, verbose_name="Distance to First Obstacle"
    )
    dominant_path = CharField(
        max_length=256,
        blank=True,
        verbose_name="Dominant Path",
        choices=(
            ("diffraction", "Diffraction"),
            ("scatter", "Scatter"),
            ("free_space", "Free Space"),
        ),
    )
    erpd_per_num_tx = CharField(
        max_length=256, blank=True, verbose_name="ERPd per # of Transmitters"
    )
    height_of_first_obstacle = FloatField(
        null=True, blank=True, verbose_name="Height of First Obstacle (ft)"
    )
    loc = CharField(max_length=256, blank=True, verbose_name="LOC")
    max_aerpd = FloatField(null=True, blank=True, verbose_name="Max AERPd (dBm)")
    max_erp_per_tx = FloatField(
        null=True, blank=True, verbose_name="Max ERP per TX (W)"
    )
    max_gain = FloatField(null=True, blank=True, verbose_name="Max Gain (dBi)")
    max_tx_power = FloatField(null=True, blank=True, verbose_name="Max TX Pwr (W)")
    nrao_aerpd = FloatField(null=True, blank=True, verbose_name="NRAO AERPd (W)")
    power_density_limit = FloatField(
        null=True, blank=True, verbose_name="Power Density Limit"
    )
    sgrs_approval = BooleanField(null=True, blank=True)
    tap_file = CharField(max_length=256, blank=True)
    tpa = CharField(max_length=256, blank=True)
    tx_power = FloatField(null=True, blank=True, verbose_name="TX Power (dBm)")
    aeirp_to_gbt = FloatField(null=True, blank=True, verbose_name="AEiRP to GBT")
    az_bearing = CharField(
        max_length=256,
        null=True,
        blank=True,
        verbose_name="AZ bearing degrees True",
        help_text="The Azimuth bearing between the Facility and the GBT, as imported from existing data",
    )
    calc_az = FloatField(
        verbose_name="Calculated Azimuth Bearing (°)",
        null=True,
        blank=True,
        help_text=(
            "Azimuth bearing between the Facility and the GBT, "
            "as calculated based on this Facility's, location"
        ),
    )
    num_tx_per_facility = IntegerField(
        null=True, blank=True, verbose_name="# of TX per facility"
    )

    nrao_approval = BooleanField(
        null=True,
        blank=True,
        help_text="Indicates whether NRAO approves of this Facility or not",
    )

    attachments = ManyToManyField("Attachment", related_name="facilities", blank=True)

    class Meta:
        verbose_name = "Facility"
        verbose_name_plural = "Facilities"

    def __iter__(self):
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    def all_fields(self):
        for field in self._meta.fields:
            yield (field.name, field.verbose_name, field.value_to_string(self))

    def __str__(self):
        if self.nrqz_id:
            nrqz_id_str = self.nrqz_id
        else:
            nrqz_id_str = "Facility"

        if self.site_num:
            nrqz_id_str += f" ({self.site_num})"
        return f"{nrqz_id_str}"

    def get_absolute_url(self):
        return reverse("facility_detail", args=[str(self.id)])

    def as_kml(self):
        return kml_to_string(facility_as_kml(self))


class PreliminaryCaseGroup(
    AbstractBaseAuditedModel, IsActiveModel, TrackedModel, DataSourceModel, Model
):
    comments = TextField(blank=True)

    class Meta:
        verbose_name = "Preliminary Case Group"
        verbose_name_plural = "Preliminary Case Groups"


class AbstractBaseCase(
    AbstractBaseAuditedModel,
    TrackedOriginalModel,
    IsActiveModel,
    TrackedModel,
    DataSourceModel,
    Model,
):

    name = CharField(max_length=256, blank=True, null=True)
    comments = TextField(blank=True)
    completed = BooleanField(default=False, blank=True, verbose_name="Completed")
    completed_on = DateTimeField(null=True, blank=True, verbose_name="Completed On")
    is_federal = BooleanField(null=True)
    num_freqs = PositiveIntegerField(null=True, blank=True, verbose_name="Num. Freq.")
    num_sites = PositiveIntegerField(null=True, blank=True, verbose_name="Num Sites")
    radio_service = CharField(max_length=256, blank=True, verbose_name="Radio Service")

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
    pcase_group = ForeignKey(
        "PreliminaryCaseGroup",
        on_delete=CASCADE,
        null=True,
        blank=True,
        related_name="prelim_cases",
    )
    case_num = PositiveIntegerField(
        unique=True, db_index=True, verbose_name="Prelim. Case Num."
    )

    case = ForeignKey(
        "Case", related_name="prelim_cases", on_delete=CASCADE, null=True, blank=True
    )

    attachments = ManyToManyField("Attachment", related_name="prelim_cases", blank=True)

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
        unique=True, db_index=True, verbose_name="Case Num."
    )

    attachments = ManyToManyField("Attachment", related_name="cases", blank=True)

    # From Access
    shutdown = BooleanField(default=False, blank=True, verbose_name="Shut Down")
    sgrs_notify = BooleanField(default=False, blank=True, verbose_name="SGRS Notified")
    sgrs_responded_on = DateTimeField(
        null=True, blank=True, verbose_name="SGRS Responded On"
    )
    # TODO: Propagate to Facility
    call_sign = CharField(max_length=256, blank=True, verbose_name="Call Sign")
    freq_coord = CharField(max_length=256, blank=True, verbose_name="Freq. Coord.")
    fcc_file_num = CharField(max_length=256, blank=True, verbose_name="FCC File Num.")
    num_outside = PositiveIntegerField(
        null=True, blank=True, verbose_name="Num. Sites Outside NRQZ"
    )
    erpd_limit = BooleanField(default=False, blank=True, verbose_name="ERPD Limit")
    si_waived = BooleanField(default=False, blank=True, verbose_name="SI Waived")
    si = BooleanField(default=False, blank=True, verbose_name="SI")
    si_done = DateField(null=True, blank=True, verbose_name="SI Done")
    date_recorded = DateTimeField(null=True, blank=True, verbose_name="Date Recorded")

    sgrs_service_num = PositiveIntegerField(null=True, blank=True)
    agency_num = CharField(max_length=256, null=True, blank=True)

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

    @property
    def nrao_approval(self):
        approvals = self.facilities.values("nrao_approval").distinct()
        if not approvals.exists() or approvals.filter(nrao_approval=None).exists():
            return None
        if approvals.filter(nrao_approval=False).exists():
            return False

        return True

    @property
    def sgrs_approval(self):
        """Return the overall SGRS Approval status of this case

        If any Facilites have not yet been approved/denied, return None,
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


class Person(
    AbstractBaseAuditedModel, IsActiveModel, TrackedModel, DataSourceModel, Model
):
    """A single, physical person"""

    name = CharField(max_length=256)
    phone = CharField(max_length=256, blank=True)
    fax = CharField(max_length=256, blank=True)
    email = EmailField(null=True, blank=True)
    street = CharField(max_length=256, blank=True)
    city = CharField(max_length=256, blank=True)
    county = CharField(max_length=256, blank=True)
    state = CharField(max_length=256, blank=True)
    zipcode = CharField(max_length=256, blank=True)
    comments = TextField(blank=True)

    # organization = ForeignKey("Organization", on_delete=CASCADE)

    def __str__(self):
        return f"{self.name}"

    def get_absolute_url(self):
        return reverse("person_detail", args=[str(self.id)])

    class Meta:
        verbose_name_plural = "People"


class AlsoKnownAs(IsActiveModel, TrackedModel, DataSourceModel, Model):
    person = ForeignKey("Person", on_delete=CASCADE, related_name="aka")
    name = CharField(max_length=256)

    def __str__(self):
        return self.name


class Attachment(
    AbstractBaseAuditedModel, IsActiveModel, TrackedModel, DataSourceModel, Model
):
    """Holds the path to a file along with some metadata"""

    # TODO: This will need to be a proper FilePathField eventually...
    path = CharField(max_length=256, unique=True)
    # path = FilePathField(path=settings.NRQZ_ATTACHMENT_DIR, max_length=256, unique=True)
    comments = TextField(blank=True)
    original_index = PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.path}"

    def get_absolute_url(self):
        return reverse("attachment_detail", args=[str(self.id)])


class LetterTemplate(IsActiveModel, TrackedModel, Model):
    name = CharField(max_length=256, unique=True)
    path = FilePathField(
        path=settings.NRQZ_LETTER_TEMPLATE_DIR, max_length=512, unique=True
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Letter Template"
        verbose_name_plural = "Letter Templates"


class Boundaries(IsActiveModel, Model):
    name = CharField(max_length=64, default=None, unique=True)
    bounds = PolygonField(geography=True, srid=4326)

    @cached_property
    def area(self):
        return (
            Boundaries.objects.filter(id=self.id)
            .annotate(area=Area(F("bounds")))
            .values("area")
            .last()["area"]
        )


class Location(IsActiveModel, Model):
    name = CharField(max_length=64, default=None, unique=True)
    location = PointField(geography=True, srid=4326)
