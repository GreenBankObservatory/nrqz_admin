from django.contrib import admin
from django.apps import apps

from django_import_data.models import (
    ModelImportAttempt,
    FileImporter,
    FileImportAttempt,
)


@admin.register(FileImporter)
class FileImporterAdmin(admin.ModelAdmin):
    fields = ("file_path",)


admin.site.register([ModelImportAttempt, FileImportAttempt])
