from django.contrib import admin

from .forms import (
    AttachmentForm,
    BoundariesForm,
    CaseAdminForm,
    # CaseGroupForm,
    FacilityForm,
    LocationForm,
    PersonForm,
    PreliminaryFacilityForm,
    PreliminaryCaseForm,
)
from .models import (
    Attachment,
    Boundaries,
    Case,
    CaseGroup,
    Facility,
    LetterTemplate,
    Location,
    Person,
    PreliminaryCase,
    PreliminaryFacility,
)


admin.site.site_header = "NRQZ Admin"


class PreliminaryCaseInline(admin.TabularInline):
    model = PreliminaryCase
    fields = (
        "id",
        "case_num",
        "applicant",
        "contact",
        "date_received",
        "completed",
        "is_federal",
        "comments",
    )
    extra = 0
    # autocomplete_fields = ["applicant", "contact"]
    readonly_fields = ["applicant", "contact"]


@admin.register(CaseGroup)
class CaseGroupAdmin(admin.ModelAdmin):
    exclude = ("model_import_attempt",)
    autocomplete_fields = ["cases", "pcases"]


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
    form = CaseAdminForm
    search_fields = ["case_num", "applicant__name", "contact__name"]
    list_display = [
        "case_num",
        "applicant",
        "contact",
        "call_sign",
        # "fcc_coord",
        "fcc_file_num",
        # "meets_erpd_limit",
        # "sgrs_approval",
        "date_received",
        "completed",
        # "comments",
        "is_federal",
    ]
    autocomplete_fields = ["applicant", "contact", "attachments"]
    ordering = ("-case_num",)
    # add_form_template = "cases/case_add_form.html"
    change_form_template = "cases/case_change_form.html"


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    form = PersonForm
    search_fields = ["name"]


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    form = AttachmentForm
    search_fields = ["file_path"]


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
    list_display = ["name", "path", "description"]
