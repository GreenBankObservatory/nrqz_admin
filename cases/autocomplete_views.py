from django import http
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
    # People can be created if given only the name
    create_field = "name"

    def get_queryset(self):
        person = Person.objects.order_by("name")
        if self.q:
            person = person.filter(name__icontains=self.q).order_by("name")
        return person


class AttachmentAutocompleteView(autocomplete.Select2QuerySetView):
    # Attachments can be created if given only the file path
    create_field = "file_path"

    def get_queryset(self):
        attachment = Attachment.objects.order_by("file_path")
        if self.q:
            self.q = Attachment.clean_path(self.q)
            attachment = attachment.filter(file_path__icontains=self.q).order_by(
                "file_path"
            )
        return attachment

    def get_result_label(self, result):
        label = super().get_result_label(result)
        return Attachment.clean_path(label)

    # Had to override this method in full, because I don't see any way to
    # manipulate q before it gets to get_create_option
    def render_to_response(self, context):
        """Return a JSON response in Select2 format."""
        q = self.request.GET.get("q", None)

        # Strip leading/trailing quotes here so that the creation option
        # works correctly (previously it was showing Create even though
        # there was already something matching the _clean_ path)
        if q:
            q = Attachment.clean_path(q)

        create_option = self.get_create_option(context, q)

        return http.JsonResponse(
            {
                "results": self.get_results(context) + create_option,
                "pagination": {"more": self.has_more(context)},
            }
        )


class CaseGroupAutocompleteView(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        case_groups = CaseGroup.objects.order_by("id")
        if self.q:
            case_groups = case_groups.filter(id__contains=self.q)
        return case_groups
