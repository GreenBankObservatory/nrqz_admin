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
    OneToOneField,
    PositiveIntegerField,
    TextField,
)

from submission.mixins import IsActiveModel, TrackedModel


class Applicant(IsActiveModel, TrackedModel, Model):
    created_on = DateTimeField(null=True)
    modified_on = DateTimeField(null=True)

    submission = OneToOneField("submission.Submission", null=True, blank=True, on_delete="PROTECT", verbose_name="Submission")
    comments = TextField(null=True, blank=True)
    applicant = CharField(max_length=256, blank=True)
    contact = CharField(max_length=256, blank=True)
    phone = CharField(max_length=256, blank=True)
    fax = CharField(max_length=256, blank=True)
    email = EmailField(null=True, blank=True)
    street = CharField(max_length=256, blank=True)
    city = CharField(max_length=256, blank=True)
    county = CharField(max_length=256, blank=True)
    state = CharField(max_length=256, blank=True)
    zipcode = CharField(max_length=256, blank=True)
    completed = BooleanField(default=False, blank=True)
    shutdown = BooleanField(default=False, blank=True)
    completed_on = DateTimeField(null=True)
    sgrs_notify = BooleanField(default=False, blank=True)
    sgrs_notified_on = DateTimeField(null=True)
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
    si_done = DateTimeField(null=True)
    letter1 = FileField(max_length=256, upload_to="attachments/")
    letter2 = FileField(max_length=256, upload_to="attachments/")
    letter3 = FileField(max_length=256, upload_to="attachments/")
    letter4 = FileField(max_length=256, upload_to="attachments/")
    letter5 = FileField(max_length=256, upload_to="attachments/")
    letter6 = FileField(max_length=256, upload_to="attachments/")
    letter7 = FileField(max_length=256, upload_to="attachments/")
    letter8 = FileField(max_length=256, upload_to="attachments/")

    # @property
    # def sgrs_notified(self):
    #     return bool(self.sgrs_notified_on)

    # @property
    # def si(self):
    #     return bool(self.si_done)

    def __str__(self):
        return f"{self.applicant} <{self.submission}>"

    def get_absolute_url(self):
        return reverse("applicant_detail", args=[str(self.id)])
