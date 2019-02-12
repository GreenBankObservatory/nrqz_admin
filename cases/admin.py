from django.contrib import admin
from django.apps import apps

# Register all models
# models = apps.get_app_config("cases").get_models()
# admin.site.register(models)

from .forms import (
    AttachmentForm,
    CaseForm,
    FacilityForm,
    PersonForm,
    PreliminaryCaseForm,
    PreliminaryFacilityForm,
)
from .models import (
    Attachment,
    Case,
    Facility,
    Person,
    PreliminaryCase,
    PreliminaryFacility,
)


@admin.register(PreliminaryFacility)
class PreliminaryFacilityAdmin(admin.ModelAdmin):
    form = PreliminaryFacilityForm
    autocomplete_fields = ["pcase", "attachments"]
    search_fields = ["pcase__case_num"]


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    form = FacilityForm
    autocomplete_fields = ["case", "attachments"]
    search_fields = ["case__case_num"]


@admin.register(PreliminaryCase)
class PreliminaryCaseAdmin(admin.ModelAdmin):
    form = PreliminaryCaseForm
    search_fields = [
        "case_num",
        "applicant__name",
        "contact__name",
        "attachments__path",
    ]


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    form = CaseForm
    search_fields = [
        "case_num",
        "applicant__name",
        "contact__name",
        "attachments__path",
    ]


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    form = PersonForm
    search_fields = ["name"]


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    search_fields = ["path"]
