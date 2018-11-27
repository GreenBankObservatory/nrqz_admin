from django.db import models
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder


class DjangoErrorJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, ValidationError):
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


class ObjectAudit(models.Model):
    linked_object = NotImplemented
    errors = JSONField(encoder=DjangoErrorJSONEncoder)

    objects = ObjectAuditManager()

    def __str__(self):
        exists_str = "exists" if self.exists else "doesn't exist"
        return f"{self.linked_object} {exists_str}"

    class Meta:
        abstract = True

    @property
    def exists(self):
        """Indicates whether the linked_object actually exists or not"""

        return bool(self.linked_object)


class BatchAudit(ObjectAudit):
    linked_object = models.ForeignKey(
        "cases.Batch", on_delete=models.SET_NULL, null=True, blank=True
    )


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
