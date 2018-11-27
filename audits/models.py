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


class ObjectAuditManager(models.Manager):
    def create_with_audit(self, form):
        """Create `linked_object` from `form` and save any errors"""

        if form.is_valid():
            linked_object = form.save()
        else:
            linked_object = None
        useful_errors = {
            field: {"value": form[field].value(), "errors": errors}
            for field, errors in form.errors.as_data().items()
        }

        return self.create(linked_object=linked_object, errors=useful_errors)


class ObjectAudit(IsActiveModel, TrackedModel, models.Model):
    linked_object = NotImplemented
    errors = JSONField(encoder=DjangoErrorJSONEncoder)
    error_summary = JSONField(encoder=DjangoErrorJSONEncoder)
    status = models.CharField(
        max_length=16,
        choices=(
            ("rejected", "Rejected (fatal errors)"),
            ("created_dirty", "Created: Some Errors"),
            ("created_clean", "Created: No Errors"),
        ),
        blank=True,
    )

    objects = ObjectAuditManager()

    class Meta:
        abstract = True

    @property
    def exists(self):
        """Indicates whether the linked_object actually exists or not"""

        return bool(self.linked_object)

    def save(self, *args, **kwargs):
        if self.linked_object:
            if self.errors:
                self.status = "created_dirty"
            else:
                self.status = "created_clean"
        else:
            self.status = "rejected"
        super(ObjectAudit, self).save(*args, **kwargs)


class BatchAudit(ObjectAudit):
    linked_object = models.ForeignKey(
        "cases.Batch", on_delete=models.SET_NULL, null=True, blank=True
    )
    original_file = models.CharField(max_length=512)

    def __str__(self):
        return os.path.basename(self.original_file)

    def get_absolute_url(self):
        return reverse("batch_audit_detail", args=[str(self.id)])


class CaseAudit(ObjectAudit):
    linked_object = models.ForeignKey(
        "cases.Case", on_delete=models.SET_NULL, null=True, blank=True
    )


class FacilityAudit(ObjectAudit):
    linked_object = models.ForeignKey(
        "cases.Facility", on_delete=models.SET_NULL, null=True, blank=True
    )


class AttachmentAudit(ObjectAudit):
    linked_object = models.ForeignKey(
        "cases.Attachment", on_delete=models.SET_NULL, null=True, blank=True
    )
