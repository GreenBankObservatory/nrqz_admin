from dal import autocomplete

from .models import (
    Attachment,
    PreliminaryCase,
    Case,
    PreliminaryFacility,
    Facility,
    Person,
    LetterTemplate,
    Structure,
    CaseGroup,
)


class PreliminaryCaseAutocompleteView(autocomplete.Select2QuerySetView):
    # model_field_name = "case_num"

    def get_queryset(self):
        cases = PreliminaryCase.objects.order_by("case_num")
        if self.q:
            cases = cases.filter(case_num__istartswith=self.q).order_by("case_num")
        return cases

    def get_result_value(self, result):
        """Return the value of a result."""
        return str(result.case_num)


class CaseAutocompleteView(autocomplete.Select2QuerySetView):
    # model_field_name = "case_num"

    def get_queryset(self):
        cases = Case.objects.order_by("case_num")
        if self.q:
            cases = cases.filter(case_num__istartswith=self.q).order_by("case_num")
        return cases

    def get_result_value(self, result):
        """Return the value of a result."""
        return str(result.case_num)


class PreliminaryFacilityAutocompleteView(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        pfacilities = PreliminaryFacility.objects.order_by("nrqz_id", "id")
        if self.q:
            pfacilities = pfacilities.filter(nrqz_id__icontains=self.q)
        return pfacilities


class FacilityAutocompleteView(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        facilities = Facility.objects.order_by("nrqz_id", "id")
        if self.q:
            facilities = facilities.filter(nrqz_id__icontains=self.q)
        return facilities


class PersonAutocompleteView(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        person = Person.objects.order_by("name")
        if self.q:
            person = person.filter(name__icontains=self.q).order_by("name")
        return person


class AttachmentAutocompleteView(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        attachment = Attachment.objects.order_by("path")
        if self.q:
            attachment = attachment.filter(path__icontains=self.q).order_by("path")
        return attachment


class CaseGroupAutocompleteView(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        case_groups = CaseGroup.objects.order_by("id")
        if self.q:
            case_groups = case_groups.filter(id__contains=self.q)
        return case_groups
