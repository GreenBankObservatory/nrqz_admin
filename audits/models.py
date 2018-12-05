import os

from django.urls import reverse
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder

from cases.mixins import IsActiveModel, TrackedModel


class DjangoErrorJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Exception):
            return repr(obj)
        return super().default(obj)


class AuditGroup(IsActiveModel, TrackedModel, models.Model):
    """Groups a set of ObjectAudits together

    Consider this case: A series of ObjectAudits are created,
    but no linked_object ever gets created. How are these to be
    associated with one another?
    """

    status = models.CharField(
        max_length=16,
        choices=(
            ("rejected", "Rejected: Fatal Errors"),
            ("created_dirty", "Imported: Some Errors"),
            ("created_clean", "Imported: No Errors"),
            ("pending", "Pending"),
        ),
        default="pending",
    )


class BatchAuditGroup(AuditGroup):
    batch = models.OneToOneField(
        "cases.Batch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_group",
    )

    def get_absolute_url(self):
        return reverse("batch_audit_group_detail", args=[str(self.id)])


class ObjectAudit(IsActiveModel, TrackedModel, models.Model):
    audit_group = models.ForeignKey(
        "BatchAuditGroup", related_name="audits", on_delete=models.CASCADE
    )
    errors = JSONField(encoder=DjangoErrorJSONEncoder)
    error_summary = JSONField(encoder=DjangoErrorJSONEncoder)
    status = models.CharField(
        max_length=16,
        choices=(
            ("rejected", "Rejected: Fatal Errors"),
            ("created_dirty", "Imported: Some Errors"),
            ("created_clean", "Imported: No Errors"),
            ("pending", "Pending"),
        ),
        default="pending",
    )

    # objects = ObjectAuditManager()

    class Meta:
        abstract = True
        ordering = ["-created_on"]

    def save(self, *args, **kwargs):
        # TODO: This is a little weird, but alright...
        self.audit_group.status = self.status
        self.audit_group.save()
        super(ObjectAudit, self).save(*args, **kwargs)


class BatchAudit(ObjectAudit):
    original_file = models.CharField(max_length=512)

    def __str__(self):
        return os.path.basename(self.original_file)

    def get_absolute_url(self):
        return reverse("batch_audit_detail", args=[str(self.id)])
