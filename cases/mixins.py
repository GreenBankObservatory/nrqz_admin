from django.db import models


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
            ("web", "Web"),
            ("excel", "Excel"),
            ("access_prelim_technical", "Access Prelim. Technical Table"),
            ("access_technical", "Access Technical Table"),
            ("access_prelim_application", "Access Prelim. Application Table"),
            ("access_application", "Access Application Table"),
        ),
        help_text="The source that this object was created from",
    )

    class Meta:
        abstract = True
