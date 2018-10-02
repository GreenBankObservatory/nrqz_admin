from django.contrib import admin
from django.apps import apps

# Register all models
models = apps.get_app_config("submission").get_models()
admin.site.register(models)
