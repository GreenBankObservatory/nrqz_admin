from django.urls import reverse
from django.db.models import (
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    EmailField,
    FileField,
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
)
from django.contrib.gis.db.models import PointField

from django_import_data.models import AuditedModel

from utils.coord_utils import dd_to_dms
from .kml import facility_as_kml, case_as_kml, kml_to_string
from .mixins import DataSourceModel, TrackedOriginalModel, IsActiveModel, TrackedModel


class Structure(IsActiveModel, TrackedModel, DataSourceModel, Model):
    asr = PositiveIntegerField(
        unique=True, verbose_name="Antenna Registration Number", db_index=True
    )
    file_num = CharField(max_length=256, verbose_name="File Number")
    location = PointField(spatial_index=True, geography=True, verbose_name="Location")
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


class PreliminaryFacility(
    TrackedOriginalModel, IsActiveModel, TrackedModel, DataSourceModel, Model
):
    # From Access
    site_num = PositiveIntegerField(verbose_name="Site #", blank=True, null=True)
    freq_low = FloatField(
        verbose_name="Freq Low (MHz)",
        help_text="Frequency specific or lower part of band.",
        null=True,
        blank=True,
    )
    antenna_model_number = CharField(
        verbose_name="Antenna Model No.", max_length=256, blank=True, null=True
    )
    power_density_limit = FloatField(
        null=True, blank=True, verbose_name="Power Density Limit"
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
    amsl = FloatField(
        verbose_name="AMSL (meters)",
        help_text="Ground elevation",
        blank=True,
        null=True,
    )
    agl = FloatField(
        verbose_name="AGL (meters)",
        help_text="Facility height to center above ground level",
        blank=True,
        null=True,
    )
    comments = TextField(
        null=True,
        blank=True,
        help_text="Additional information or comments from the applicant",
    )

    location = PointField(blank=True, null=True, spatial_index=True, geography=True)
    pcase = ForeignKey("PreliminaryCase", on_delete=CASCADE, related_name="pfacilities")

    class Meta:
        verbose_name = "Preliminary Facility"
        verbose_name_plural = "Preliminary Facilities"

    def __str__(self):
        return f"{self.antenna_model_number} <{self.id}>"

    def get_absolute_url(self):
        return reverse("prelim_facility_detail", args=[str(self.id)])


class Facility(
    TrackedOriginalModel, IsActiveModel, TrackedModel, DataSourceModel, Model
):
    """Describes a single, physical antenna"""

    freq_low = FloatField(
        verbose_name="Freq Low (MHz)",
        help_text="Frequency specific or lower part of band.",
        null=True,
        blank=True,
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
        help_text="(optional)",
    )
    fcc_file_number = CharField(
        max_length=256,
        blank=True,
        null=True,
        verbose_name="FCC File Number",
        help_text="(if known)",
    )
    location = PointField(blank=True, null=True, spatial_index=True, geography=True)
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
    amsl = FloatField(
        verbose_name="AMSL (meters)",
        help_text="Ground elevation",
        blank=True,
        null=True,
    )
    agl = FloatField(
        verbose_name="AGL (meters)",
        help_text="Facility height to center above ground level",
        blank=True,
        null=True,
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
    asr_is_from_applicant = BooleanField(null=True, blank=True)
    comments = TextField(
        null=True,
        blank=True,
        help_text="Additional information or comments from the applicant",
    )

    case = ForeignKey("Case", on_delete=CASCADE, related_name="facilities")
    structure = ForeignKey(
        "Structure",
        blank=True,
        null=True,
        on_delete=SET_NULL,
        related_name="facilities",
    )

    # From Working Data
    band_allowance = FloatField(null=True, blank=True, verbose_name="Band Allowance")
    distance_to_first_obstacle = CharField(
        max_length=256, null=True, blank=True, verbose_name="Distance to First Obstacle"
    )
    dominant_path = CharField(max_length=256, blank=True, verbose_name="Dominant Path")
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
    tap = CharField(max_length=256, blank=True)
    tx_power = FloatField(null=True, blank=True, verbose_name="TX Power (dBm)")
    aeirp_to_gbt = FloatField(null=True, blank=True, verbose_name="AEiRP to GBT")
    az_bearing = CharField(
        max_length=256, null=True, blank=True, verbose_name="AZ bearing degrees True"
    )
    num_tx_per_facility = IntegerField(
        null=True, blank=True, verbose_name="# of TX per facility"
    )
    site_num = PositiveIntegerField(verbose_name="Site #", blank=True, null=True)

    class Meta:
        verbose_name_plural = "Facilities"

    def __iter__(self):
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    def __str__(self):
        return f"{self.nrqz_id} <{self.id}>"

    def get_absolute_url(self):
        return reverse("facility_detail", args=[str(self.id)])

    def as_kml(self):
        return kml_to_string(facility_as_kml(self))


class Batch(TrackedOriginalModel, IsActiveModel, TrackedModel, DataSourceModel, Model):
    comments = TextField(blank=True)
    attachments = ManyToManyField("Attachment", blank=True)
    name = CharField(max_length=256, unique=True)
    import_error_summary = TextField()
    imported_from = CharField(max_length=512, unique=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("batch_detail", args=[str(self.id)])

    class Meta:
        verbose_name_plural = "Batches"


class PreliminaryCaseGroup(IsActiveModel, TrackedModel, DataSourceModel, Model):
    comments = TextField(blank=True)

    class Meta:
        verbose_name = "Preliminary Case Group"
        verbose_name_plural = "Preliminary Case Groups"


class PreliminaryCase(
    TrackedOriginalModel, IsActiveModel, TrackedModel, DataSourceModel, Model
):
    applicant = ForeignKey(
        "Person",
        on_delete=SET_NULL,
        related_name="applicant_for_prelim_cases",
        null=True,
        blank=True,
    )
    contact = ForeignKey(
        "Person",
        on_delete=SET_NULL,
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
    comments = TextField(blank=True)
    case_num = PositiveIntegerField(
        unique=True, db_index=True, verbose_name="Prelim. Case Num."
    )
    name = CharField(max_length=256, blank=True, null=True)

    case = ForeignKey(
        "Case", related_name="prelim_cases", on_delete=SET_NULL, null=True, blank=True
    )

    attachments = ManyToManyField("Attachment", related_name="prelim_cases", blank=True)

    completed = BooleanField(default=False, blank=True, verbose_name="Completed")
    completed_on = DateTimeField(null=True, blank=True, verbose_name="Completed On")
    radio_service = CharField(max_length=256, blank=True, verbose_name="Radio Service")
    num_freqs = PositiveIntegerField(null=True, blank=True, verbose_name="Num. Freq.")
    num_sites = PositiveIntegerField(null=True, blank=True, verbose_name="Num Sites")

    # Misc.
    slug = SlugField(unique=True)

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


class Case(
    AuditedModel,
    TrackedOriginalModel,
    IsActiveModel,
    TrackedModel,
    DataSourceModel,
    Model,
):
    """Defines a given NRQZ Application"""

    # sites = ManyToManyField("Site")
    applicant = ForeignKey(
        "Person",
        on_delete=SET_NULL,
        related_name="applicant_for_cases",
        null=True,
        blank=True,
    )
    contact = ForeignKey(
        "Person",
        on_delete=SET_NULL,
        related_name="contact_for_cases",
        null=True,
        blank=True,
    )
    comments = TextField(blank=True)
    case_num = PositiveIntegerField(
        unique=True, db_index=True, verbose_name="Case Num."
    )
    name = CharField(max_length=256, blank=True, null=True)

    batch = ForeignKey(
        "Batch", related_name="cases", on_delete=CASCADE, null=True, blank=True
    )

    attachments = ManyToManyField("Attachment", related_name="cases", blank=True)

    # From Access
    completed = BooleanField(default=False, blank=True, verbose_name="Completed")
    shutdown = BooleanField(default=False, blank=True, verbose_name="Shut Down")
    completed_on = DateTimeField(null=True, blank=True, verbose_name="Completed On")
    sgrs_notify = BooleanField(default=False, blank=True, verbose_name="SGRS Notified")
    sgrs_notified_on = DateTimeField(
        null=True, blank=True, verbose_name="SGRS Notified On"
    )
    radio_service = CharField(max_length=256, blank=True, verbose_name="Radio Service")
    call_sign = CharField(max_length=256, blank=True, verbose_name="Call Sign")
    freq_coord = CharField(max_length=256, blank=True, verbose_name="Freq. Coord.")
    fcc_file_num = CharField(max_length=256, blank=True, verbose_name="FCC File Num.")
    num_freqs = PositiveIntegerField(null=True, blank=True, verbose_name="Num. Freq.")
    num_sites = PositiveIntegerField(null=True, blank=True, verbose_name="Num Sites")
    num_outside = PositiveIntegerField(
        null=True, blank=True, verbose_name="Num. Sites Outside NRQZ"
    )
    erpd_limit = BooleanField(default=False, blank=True, verbose_name="ERPD Limit")
    si_waived = BooleanField(default=False, blank=True, verbose_name="SI Waived")
    si = BooleanField(default=False, blank=True, verbose_name="SI")
    si_done = DateTimeField(null=True, blank=True, verbose_name="SI Done")

    # Misc.
    slug = SlugField(unique=True)

    def __str__(self):
        return f"{self.case_num}"

    def get_absolute_url(self):
        return reverse("case_detail", args=[str(self.case_num)])

    def as_kml(self):
        return kml_to_string(case_as_kml(self))

    def save(self, *args, **kwargs):
        self.slug = str(self.case_num)
        super(Case, self).save(*args, **kwargs)


class Person(AuditedModel, IsActiveModel, TrackedModel, DataSourceModel, Model):
    """A single, physical person"""

    name = CharField(max_length=256, blank=True)
    phone = CharField(max_length=256, blank=True)
    fax = CharField(max_length=256, blank=True)
    email = EmailField(null=True, blank=True)
    street = CharField(max_length=256, blank=True)
    city = CharField(max_length=256, blank=True)
    county = CharField(max_length=256, blank=True)
    state = CharField(max_length=256, blank=True)
    zipcode = CharField(max_length=256, blank=True)
    comments = TextField(blank=True)

    # organization = ForeignKey("Organization", on_delete=SET_NULL)

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


class Attachment(IsActiveModel, TrackedModel, DataSourceModel, Model):
    """Holds the path to a file along with some metadata"""

    # TODO: This will need to be a proper FileField eventually...
    path = CharField(max_length=256, unique=True)
    # path = FileField(max_length=256, upload_to="attachments/")
    comments = TextField()

    def __str__(self):
        return f"{self.path}"

    def get_absolute_url(self):
        return reverse("attachment_detail", args=[str(self.id)])


class LetterTemplate(IsActiveModel, TrackedModel, Model):
    name = CharField(max_length=256, unique=True)
    template = TextField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Letter Template"
        verbose_name_plural = "Letter Templates"
