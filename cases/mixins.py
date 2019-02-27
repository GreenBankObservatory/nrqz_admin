from django.db import models
from utils.constants import (
    ACCESS_APPLICATION,
    ACCESS_PRELIM_APPLICATION,
    ACCESS_PRELIM_TECHNICAL,
    ACCESS_TECHNICAL,
    EXCEL,
    FCC_ASR,
    NAM_APPLICATION,
    WEB,
)


class IsActiveModel(models.Model):
    """An abstract class that allows objects to be 'soft' deleted.
    """

    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class TrackedOriginalModel(models.Model):
    original_created_on = models.DateTimeField(null=True, blank=True)
    original_modified_on = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


class TrackedModel(models.Model):
    """An abstract class for any models that need to track who
    created or last modified an object and when.
    """

    # Django sets these fields automagically for us when objs are saved!
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)
    # We'll have to set these ourselves
    # created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
    #                                related_name="%(class)s_created",
    #                                on_delete=models.PROTECT)
    # modified_by = models.ForeignKey(settings.AUTH_USER_MODEL,
    #                                 related_name="%(class)s_modified",
    #                                 null=True,
    #                                 on_delete=models.PROTECT)

    class Meta:
        abstract = True

    # def set_created_modified_by(self, profile):
    #     # created_by, modified_by are required fields set by API;
    #     # but we want to make it easy to set these from the shell
    #     if not hasattr(self, 'created_by') or self.created_by is None:
    #         self.created_by = profile
    #     if not hasattr(self, 'modified_by') or self.modified_by is None:
    #         self.modified_by = profile


class DataSourceModel(models.Model):
    data_source = models.CharField(
        max_length=25,
        choices=(
            (WEB, "Web"),
            (EXCEL, "Excel"),
            (ACCESS_PRELIM_TECHNICAL, "Access Prelim. Technical Table"),
            (ACCESS_TECHNICAL, "Access Technical Table"),
            (ACCESS_PRELIM_APPLICATION, "Access Prelim. Application Table"),
            (ACCESS_APPLICATION, "Access Application Table"),
            (NAM_APPLICATION, "NRQZ Analyzer Application"),
            (FCC_ASR, "FCC ASR Database"),
        ),
        help_text="The source that this object was created from",
        default=None,
    )

    class Meta:
        abstract = True


class AllFieldsModel(models.Model):
    def all_fields(self):
        for field in self._meta.fields:
            yield (field.name, field.verbose_name, field.value_to_string(self))

    class Meta:
        abstract = True
