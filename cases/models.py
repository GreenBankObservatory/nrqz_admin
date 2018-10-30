from django.urls import reverse
from django.db.models import (
    BooleanField,
    CharField,
    DateTimeField,
    DecimalField,
    EmailField,
    FileField,
    ForeignKey,
    IntegerField,
    ManyToManyField,
    Model,
    PositiveIntegerField,
    TextField,
    PROTECT,
    SET_NULL,
    SlugField,
)
from django.contrib.gis.db.models import PointField

from utils.coord_utils import dd_to_dms
from .kml import facility_as_kml, case_as_kml, kml_to_string
from .mixins import IsActiveModel, TrackedModel


class CoordinateField(DecimalField):
    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        d, m, s = dd_to_dms(value)
        return f"{d:03d} {m:02d} {s:2.3f}"


class Facility(IsActiveModel, TrackedModel, Model):
    """Describes a single, physical antenna"""

    freq_low = DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Freq Low (MHz)",
        help_text="Frequency specific or lower part of band.",
        null=True,
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
    location = PointField(null=True, spatial_index=True, geography=True)
    latitude = CoordinateField(
        null=True,
        max_digits=10,
        decimal_places=8,
        verbose_name="Latitude",
        help_text="Latitude of site, in degrees",
    )
    longitude = CoordinateField(
        null=True,
        max_digits=10,
        decimal_places=8,
        verbose_name="Longitude",
        help_text="Longitude of site, in degrees",
    )
    amsl = DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="AMSL (meters)",
        help_text="Ground elevation",
        null=True,
    )
    agl = DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="AGL (meters)",
        help_text="Facility height to center above ground level",
        null=True,
    )
    freq_high = DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Freq High (MHz)",
        help_text="Frequency specific or upper part of band.",
        null=True,
    )
    bandwidth = DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Bandwidth (MHz)",
        help_text="Minimum utilized per TX (i.e. 11K0F0E is a value of 0.011)",
        null=True,
    )
    max_output = DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Max Output Pwr (W)",
        help_text="Per Transmitter or RRH (remote radio head) polarization",
        null=True,
    )
    antenna_gain = DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Antenna Gain (dBi)", null=True
    )
    system_loss = IntegerField(verbose_name="System Loss (dB)", blank=True, null=True)
    main_beam_orientation = CharField(
        max_length=256,
        verbose_name="Main Beam Orientation",
        help_text="or sectorized AZ bearings (in ° True NOT ° Magnetic)",
    )
    mechanical_downtilt = CharField(
        verbose_name="Mechanical Downtilt", max_length=256, blank=True, null=True
    )
    electrical_downtilt = CharField(
        verbose_name="Electrical Downtilt Sector",
        max_length=256,
        blank=True,
        null=True,
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
    tx_power_pos_45 = DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Max TX output PWR at +45 degrees",
    )
    tx_power_neg_45 = DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Max TX output PWR at -45 degrees",
    )
    comments = TextField(
        help_text="Additional information or comments from the applicant"
    )

    case = ForeignKey("Case", on_delete=PROTECT, related_name="facilities")

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


class Batch(IsActiveModel, TrackedModel, Model):
    comments = TextField(blank=True)
    attachments = ManyToManyField("Attachment")
    name = CharField(max_length=256, blank=True, null=True)
    import_error_summary = TextField()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("batch_detail", args=[str(self.id)])


class Case(IsActiveModel, TrackedModel, Model):
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
    case_num = PositiveIntegerField(unique=True)
    name = CharField(max_length=256, blank=True, null=True)

    batch = ForeignKey("Batch", related_name="cases", on_delete=SET_NULL, null=True, blank=True)

    attachments = ManyToManyField("Attachment", related_name="cases", blank=True)

    # From Access
    completed = BooleanField(default=False, blank=True)
    shutdown = BooleanField(default=False, blank=True)
    completed_on = DateTimeField(null=True, blank=True)
    sgrs_notify = BooleanField(default=False, blank=True)
    sgrs_notified_on = DateTimeField(null=True, blank=True)
    radio_service = CharField(max_length=256, blank=True)
    call_sign = CharField(max_length=256, blank=True)
    fcc_freq_coord = CharField(max_length=256, blank=True)
    fcc_file_num = CharField(max_length=256, blank=True)
    num_freqs = PositiveIntegerField(null=True, blank=True)
    num_sites = PositiveIntegerField(null=True, blank=True)
    num_outside = PositiveIntegerField(null=True, blank=True)
    erpd_limit = BooleanField(default=False, blank=True)
    si_waived = BooleanField(default=False, blank=True)
    si = BooleanField(default=False, blank=True)
    si_done = DateTimeField(null=True, blank=True)

    slug = SlugField(unique=True)

    def __str__(self):
        return f"{self.case_num}"

    def get_absolute_url(self):
        return reverse("case_detail", args=[str(self.id)])

    def as_kml(self):
        return kml_to_string(case_as_kml(self))

    def save(self, *args, **kwargs):
        self.slug = str(self.case_num)
        super(Case, self).save(*args, **kwargs)



class Person(IsActiveModel, TrackedModel, Model):
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


class Attachment(IsActiveModel, TrackedModel, Model):
    """Holds the path to a file along with some metadata"""

    # TODO: This will need to be a proper FileField eventually...
    path = CharField(max_length=256)
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
