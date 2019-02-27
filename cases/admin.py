from django.contrib import admin
from django.apps import apps

# Register all models
# models = apps.get_app_config("cases").get_models()
# admin.site.register(models)

from .forms import (
    AttachmentForm,
    BoundariesForm,
    CaseForm,
    FacilityForm,
    LocationForm,
    PersonForm,
    PreliminaryCaseForm,
    PreliminaryFacilityForm,
)
from .models import (
    Attachment,
    Boundaries,
    Case,
    Facility,
    Location,
    Person,
    PreliminaryCase,
    PreliminaryFacility,
    LetterTemplate,
)


@admin.register(PreliminaryFacility)
class PreliminaryFacilityAdmin(admin.ModelAdmin):
    form = PreliminaryFacilityForm
    # autocomplete_fields = ["pcase", "attachments"]
    search_fields = ["pcase__case_num"]
    ordering = ("-pcase__case_num",)


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    form = FacilityForm
    # autocomplete_fields = ["case", "attachments"]
    search_fields = ["case__case_num"]
    ordering = ("-case__case_num",)


@admin.register(PreliminaryCase)
class PreliminaryCaseAdmin(admin.ModelAdmin):
    form = PreliminaryCaseForm
    search_fields = ["case_num", "applicant__name", "contact__name"]
    ordering = ("-case_num",)


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    form = CaseForm
    search_fields = ["case_num", "applicant__name", "contact__name"]
    ordering = ("-case_num",)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    form = PersonForm
    search_fields = ["name"]


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    form = AttachmentForm
    search_fields = ["path"]


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    form = LocationForm
    search_fields = ["name"]


@admin.register(Boundaries)
class BoundariesAdmin(admin.ModelAdmin):
    form = BoundariesForm
    search_fields = ["name"]


@admin.register(LetterTemplate)
class LetterTemplateAdmin(admin.ModelAdmin):
    pass
