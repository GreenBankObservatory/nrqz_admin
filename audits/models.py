# import os

# from django.urls import reverse
# from django.db import models
# from django.utils.functional import cached_property

# from django_import_data.models import BaseAuditGroup, BaseAudit

# from cases.mixins import DataSourceModel, IsActiveModel


# class BatchAuditGroup(BaseAuditGroup, IsActiveModel, DataSourceModel):
#     batch = models.OneToOneField(
#         "cases.Batch",
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="audit_group",
#     )
#     last_imported_path = models.CharField(max_length=512, unique=True)

#     @cached_property
#     def auditee(self):
#         return self.batch

#     class Meta:
#         verbose_name = "Batch Audit Group"
#         verbose_name_plural = "Batch Audit Groups"

#     def __str__(self):
#         return os.path.basename(self.last_imported_path)

#     def get_absolute_url(self):
#         return reverse("batch_audit_group_detail", args=[str(self.id)])


# class BatchAudit(BaseAudit, IsActiveModel, DataSourceModel):
#     audit_group = models.ForeignKey(
#         "BatchAuditGroup", related_name="audits", on_delete=models.CASCADE
#     )
#     original_file = models.CharField(max_length=512)

#     class Meta:
#         verbose_name = "Batch Audit"
#         verbose_name_plural = "Batch Audits"
#         ordering = ["-created_on"]

#     def __str__(self):
#         return os.path.basename(self.original_file)

#     def get_absolute_url(self):
#         return reverse("batch_audit_detail", args=[str(self.id)])

#     def save(self, *args, **kwargs):
#         # TODO: This is a little weird, but alright...
#         self.audit_group.status = self.status
#         self.audit_group.last_imported_path = self.original_file
#         self.audit_group.save()
#         super().save(*args, **kwargs)
