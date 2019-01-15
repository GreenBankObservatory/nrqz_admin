from django.contrib import admin
from django.apps import apps

# Register all models
models = apps.get_app_config("audits").get_models()
admin.site.register(models)

from django_import_data.models import ModelImportAttempt, FileImportAttempt

admin.site.register([ModelImportAttempt, FileImportAttempt])
