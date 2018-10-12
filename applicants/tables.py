import django_tables2 as tables

from . import models
from .filters import ApplicantFilter


class ApplicantTable(tables.Table):
    nrqz_no = tables.Column(linkify=True)

    class Meta:
        model = models.Applicant
        fields = ApplicantFilter.Meta.fields
