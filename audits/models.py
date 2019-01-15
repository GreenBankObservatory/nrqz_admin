# from django.db import models

# from cases.models import Case, Person, PreliminaryCase, Facility, PreliminaryFacility

# from django_import_data.models import (
#     BaseAudit,
#     BaseAuditGroup,
#     BaseBatchImport,
#     BaseAuditGroupBatch,
# )


# class PersonImporter(BaseAuditGroup):
#     importee = models.OneToOneField(
#         Person,
#         related_name="importer",
#         on_delete=models.CASCADE,
#         # help_text="Reference to the audit group that 'holds' this audit",
#         null=True,
#         blank=True,
#     )

#     @property
#     def person(self):
#         return self.importee

#     def attempt(self, **kwargs):
#         return PersonImportAttempt.objects.create(**kwargs)


# class PersonImportAttempt(BaseAudit):
#     importer = models.OneToOneField(
#         PersonImporter,
#         related_name="attempts",
#         on_delete=models.CASCADE,
#         help_text="Reference to the audit group that 'holds' this audit",
#         null=True,
#         blank=True,
#     )


# class CaseImporter(BaseAuditGroup):
#     importee = models.OneToOneField(
#         Case,
#         related_name="importer",
#         on_delete=models.CASCADE,
#         # help_text="Reference to the audit group that 'holds' this audit",
#         null=True,
#         blank=True,
#     )

#     @property
#     def case(self):
#         return self.importee

#     def attempt(self, **kwargs):
#         return CaseImportAttempt.objects.create(**kwargs)


# class CaseImportAttempt(BaseAudit):
#     importer = models.OneToOneField(
#         CaseImporter,
#         related_name="attempts",
#         on_delete=models.CASCADE,
#         help_text="Reference to the audit group that 'holds' this audit",
#         null=True,
#         blank=True,
#     )


# class PCaseImporter(BaseAuditGroup):
#     importee = models.OneToOneField(
#         PreliminaryCase,
#         related_name="importer",
#         on_delete=models.CASCADE,
#         # help_text="Reference to the audit group that 'holds' this audit",
#         null=True,
#         blank=True,
#     )

#     @property
#     def pcase(self):
#         return self.importee


# class PCaseImportAttempt(BaseAudit):
#     importer = models.OneToOneField(
#         PCaseImporter,
#         related_name="attempts",
#         on_delete=models.CASCADE,
#         help_text="Reference to the audit group that 'holds' this audit",
#         null=True,
#         blank=True,
#     )


# class FacilityImporter(BaseAuditGroup):
#     importee = models.OneToOneField(
#         Facility,
#         related_name="importer",
#         on_delete=models.CASCADE,
#         # help_text="Reference to the audit group that 'holds' this audit",
#         null=True,
#         blank=True,
#     )

#     @property
#     def facility(self):
#         return self.importee


# class FacilityImportAttempt(BaseAudit):
#     importer = models.OneToOneField(
#         FacilityImporter,
#         related_name="attempts",
#         on_delete=models.CASCADE,
#         help_text="Reference to the audit group that 'holds' this audit",
#         null=True,
#         blank=True,
#     )


# class PFacilityImporter(BaseAuditGroup):
#     importee = models.OneToOneField(
#         PreliminaryFacility,
#         related_name="importer",
#         on_delete=models.CASCADE,
#         # help_text="Reference to the audit group that 'holds' this audit",
#         null=True,
#         blank=True,
#     )

#     @property
#     def pfacility(self):
#         return self.importee


# class PFacilityImportAttempt(BaseAudit):
#     importer = models.OneToOneField(
#         PFacilityImporter,
#         related_name="attempts",
#         on_delete=models.CASCADE,
#         help_text="Reference to the audit group that 'holds' this audit",
#         null=True,
#         blank=True,
#     )
