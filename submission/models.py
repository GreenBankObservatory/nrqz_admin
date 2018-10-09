from django.urls import reverse
from django.db.models import (
    BooleanField,
    CharField,
    DecimalField,
    EmailField,
    FileField,
    ForeignKey,
    IntegerField,
    ManyToManyField,
    Model,
    PositiveIntegerField,
    TextField,
)

from .mixins import IsActiveModel, TrackedModel

# from django.contrib.gis.db.models import PointField


# class Technology(IsActiveModel, TrackedModel, Model):
#     """A type of cellular technology"""

#     class Meta:
#         verbose_name_plural = "Technologies"

#     abbrev = CharField(max_length=16)
#     name = CharField(max_length=256)

#     def __str__(self):
#         return f"{self.name} ({self.abbrev})"


# class Transmitter(IsActiveModel, TrackedModel, Model):

# class Antenna(IsActiveModel, TrackedModel, Model):
#     gain = DecimalField(
#         max_digits=10, decimal_places=2, verbose_name="Gain", help_text="Gain in dB"
#     )
#     model_num = CharField(
#         max_length=256, verbose_name="Model Number", help_text="Antenna Model Number"
#     )


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
    latitude = DecimalField(
        null=True,
        max_digits=10,
        decimal_places=8,
        verbose_name="Latitude",
        help_text="Latitude of site, in degrees",
    )
    longitude = DecimalField(
        null=True,
        max_digits=10,
        decimal_places=8,
        verbose_name="Longitude",
        help_text="Longitude of site, in degrees",
    )
    # latitude = CharField(
    #     max_length=256,
    #     null=True,
    #     help_text="Correct format is dd mm ss.ss (space seperated). No symbols or special characters!",
    # )
    # longitude = CharField(
    #     max_length=256,
    #     null=True,
    #     help_text="Correct format is dd mm ss.ss (space seperated). No symbols or special characters!",
    # )
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
    )
    tx_per_sector = PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Total number of TXers per sector",
        help_text="(or No. of RRH's ports with feed power",
    )
    tx_antennas_per_sector = PositiveIntegerField(
        blank=True, null=True, verbose_name="Number of polarizations with feed power"
    )
    num_pols_with_feed_power = PositiveIntegerField(
        blank=True, null=True, verbose_name="Number of polarizations with feed power"
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
    quad_or_octal_polarization = CharField(
        max_length=256,
        blank=True,
        null=True,
        verbose_name="If this facility uses Quad or Octal polarization, specify type here",
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

    submission = ForeignKey(
        "Submission", on_delete="PROTECT", related_name="facilities"
    )

    def __iter__(self):
        for field in self._meta.fields:
            yield (field.verbose_name, field.value_to_string(self))

    def __str__(self):
        return f"NRQZ {self.nrqz_id} ({self.latitude}, {self.longitude})"

    def get_absolute_url(self):
        return reverse("submission_facility_detail", args=[str(self.id)])


# class Site(IsActiveModel, TrackedModel, Model):
#     """Describes a single, physical site"""

#     name = CharField(
#         max_length=256, help_text="What you call it! Include MCN and eNB information."
#     )
#     lat = DecimalField(
#         max_digits=10, decimal_places=8, help_text="Latitude of site, in degrees"
#     )
#     long = DecimalField(
#         max_digits=10, decimal_places=8, help_text="Longitude of site, in degrees"
#     )


# class Polarization(IsActiveModel, TrackedModel, Model):
#     """A type of polarization"""

#     abbrev = CharField(max_length=64)
#     name = CharField(max_length=64)

#     def __str__(self):
#         return f"{self.name} ({self.abbrev})"

#     # comments = TextField()


# TODO: Change to Application
class Submission(IsActiveModel, TrackedModel, Model):
    """Defines a given NRQZ Application"""

    # sites = ManyToManyField("Site")
    # applicant = ForeignKey("Person", on_delete="PROTECT", related_name="applicant_for", null=True, blank=True)
    # contact = ForeignKey("Person", on_delete="PROTECT", related_name="contact_for", null=True, blank=True)
    comments = TextField(blank=True)

    # fcc_file_number
    # sgrs_notified = BooleanField(default=False)

    attachments = ManyToManyField("Attachment")

    import_error_summary = TextField()

    # facilities = ManyToManyField("Facility")

    def __str__(self):
        return f"Application {self.id} ({self.created_on})"


class Person(IsActiveModel, TrackedModel, Model):
    """A single, physical person"""

    name = CharField(max_length=256)
    address = CharField(max_length=256)
    email = EmailField()

    phone_num = CharField(max_length=16)
    fax_num = CharField(max_length=16)

    comments = TextField()

    organization = ForeignKey("Organization", on_delete="PROTECT")

    def __str__(self):
        return f"{self.name}"


class Organization(IsActiveModel, TrackedModel, Model):
    """A single, physical organization"""

    name = CharField(max_length=256)
    address = CharField(max_length=256)
    email = EmailField()

    phone_num = CharField(max_length=16)
    fax_num = CharField(max_length=16)

    comments = TextField()

    def __str__(self):
        return f"{self.name}"


class Attachment(IsActiveModel, TrackedModel, Model):
    """Holds the path to a file along with some metadata"""

    path = FileField(max_length=256, upload_to="attachments/")
    comments = TextField()

    def __str__(self):
        return f"{self.path}"
