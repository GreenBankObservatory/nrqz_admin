from datetime import date
import tempfile

from django.views.generic.detail import DetailView
from django.views.generic.base import TemplateView
from django.http import HttpResponse
from django.db.models import Min, Max
from django.shortcuts import get_object_or_404
from django.template import Template, Context
from django.db.models import Q

import pypandoc
from dal import autocomplete
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from .forms import LetterTemplateForm
from .models import (
    Attachment,
    Batch,
    PreliminaryCase,
    Case,
    Facility,
    Person,
    LetterTemplate,
    Structure,
    PreliminaryCaseGroup,
)
from .filters import (
    AttachmentFilter,
    BatchFilter,
    FacilityFilter,
    PersonFilter,
    PreliminaryCaseGroupFilter,
    PreliminaryCaseFilter,
    CaseFilter,
    StructureFilter,
)
from .tables import (
    AttachmentTable,
    BatchTable,
    FacilityTable,
    FacilityTableWithConcur,
    PersonTable,
    PreliminaryCaseGroupTable,
    PreliminaryCaseTable,
    CaseTable,
    LetterFacilityTable,
    StructureTable,
)
from .kml import (
    facility_as_kml,
    facilities_as_kml,
    case_as_kml,
    cases_as_kml,
    kml_to_string,
)


class FilterTableView(SingleTableMixin, FilterView):
    table_class = None
    filterset_class = None
    object_list = NotImplemented
    # table_pagination = True

    def get(self, request, *args, **kwargs):
        if "show-all" in request.GET:
            self.table_pagination = False
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # If there are no query params, then no results are
        # displayed -- but that's not what we want!
        if not self.request.GET:
            # Need this here to avoid a blank table appearing on first load
            self.object_list = self.table_class.Meta.model.objects.all()

        return super().get_context_data(**kwargs)


class BatchListView(FilterTableView):
    table_class = BatchTable
    filterset_class = BatchFilter
    template_name = "cases/batch_list.html"


class BatchDetailView(DetailView):
    model = Batch

    def __init__(self, *args, **kwargs):
        super(BatchDetailView, self).__init__(*args, **kwargs)
        self.case_filter = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.case_filter is None:
            self.case_filter = CaseFilter(
                self.request.GET,
                queryset=self.object.cases.all(),
                form_helper_kwargs={"form_class": "collapse"},
            )
            context["case_filter"] = self.case_filter

        if "case_table" not in context:
            table = CaseTable(data=self.case_filter.qs)
            table.paginate(page=self.request.GET.get("page", 1), per_page=10)
            context["case_table"] = table

        return context


class PreliminaryCaseGroupListView(FilterTableView):
    table_class = PreliminaryCaseGroupTable
    filterset_class = PreliminaryCaseGroupFilter
    template_name = "cases/prelim_case_group_list.html"


class PreliminaryCaseListView(FilterTableView):
    table_class = PreliminaryCaseTable
    filterset_class = PreliminaryCaseFilter
    template_name = "cases/prelim_case_list.html"


class CaseListView(FilterTableView):
    table_class = CaseTable
    filterset_class = CaseFilter
    template_name = "cases/case_list.html"

    def get(self, request, *args, **kwargs):
        if "kml" in request.GET:
            # TODO: Must be a cleaner way to do this
            qs = self.get_filterset(self.filterset_class).qs
            response = HttpResponse(
                kml_to_string(cases_as_kml(qs)),
                content_type="application/vnd.google-earth.kml+xml.",
            )
            response["Content-Disposition"] = 'application; filename="nrqz_apps.kml"'
            return response
        else:
            return super(CaseListView, self).get(request, *args, **kwargs)


class FacilityListView(FilterTableView):
    table_class = FacilityTable
    filterset_class = FacilityFilter
    template_name = "cases/facility_list.html"

    def get(self, request, *args, **kwargs):
        if "kml" in request.GET:
            # TODO: Must be a cleaner way to do this
            qs = self.get_filterset(self.filterset_class).qs
            response = HttpResponse(
                kml_to_string(facilities_as_kml(qs)),
                content_type="application/vnd.google-earth.kml+xml.",
            )
            response[
                "Content-Disposition"
            ] = 'application; filename="nrqz_facilities.kml"'
            return response
        else:
            return super(FacilityListView, self).get(request, *args, **kwargs)


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


class FacilityAutocompleteView(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        facilities = Facility.objects.order_by("nrqz_id", "id")
        if self.q:
            facilities = facilities.filter(nrqz_id__icontains=self.q)
        return facilities


class LetterView(TemplateView):
    template_name = "cases/concurrence_letter.html"

    def get(self, request, *args, **kwargs):
        facilities_q = Q()
        if "facilities" in request.GET:
            kwargs.update({"facilities": request.GET.getlist("facilities")})
            facilities_q |= Q(id__in=request.GET.getlist("facilities"))

        if "cases" in request.GET:
            kwargs.update({"cases": request.GET.getlist("cases")})
            facilities_q |= Q(case__case_num__in=request.GET.getlist("cases"))

        if "batches" in request.GET:
            kwargs.update({"batches": request.GET.getlist("batches")})
            facilities_q |= Q(batch__case__case_num__in=request.GET.getlist("batches"))

        if "template" in request.GET:
            kwargs.update({"template": request.GET["template"]})

        if facilities_q:
            facilities = Facility.objects.filter(facilities_q)
        else:
            facilities = Facility.objects.none()
        kwargs.update({"facilities_result": facilities})

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        facilities = context["facilities_result"]
        if "cases" in context:
            cases = Case.objects.filter(case_num__in=context["cases"])
        else:
            cases = Case.objects.none()
        context["cases"] = cases
        context["facilities"] = facilities

        letter_context = {}
        letter_context["case"] = cases.first()
        letter_context["generation_date"] = date.today().strftime("%B %d, %Y")
        letter_context["nrqz_ids"] = ", ".join(
            facilities.values_list("nrqz_id", flat=True)
        )
        if facilities:
            context["min_freq"] = (
                facilities.annotate(Min("freq_low"))
                .order_by("freq_low__min")
                .first()
                .freq_low
            )
            context["max_freq"] = (
                facilities.annotate(Max("freq_high"))
                .order_by("-freq_high__max")
                .first()
                .freq_high
            )
        table = LetterFacilityTable(data=facilities)
        letter_context["facilities_table"] = table

        if "template" in context:
            letter_template = get_object_or_404(
                LetterTemplate, name=context["template"]
            )
        else:
            try:
                letter_template = LetterTemplate.objects.get(name="default")
            except LetterTemplate.DoesNotExist:
                letter_template = LetterTemplate.objects.first()

        if letter_template:
            kwargs["template"] = letter_template.name
            form_values = {
                field: value
                for field, value in kwargs.items()
                if field in ["cases", "facilities", "batches", "template"]
            }
            context["template_form"] = LetterTemplateForm(form_values)
            context["letter_template"] = Template(letter_template.template).render(
                Context(letter_context)
            )
        else:
            kwargs["template"] = None
            context["template_form"] = None
            context["letter_template"] = None

        # Create queryset of specified facilities that are not included in any
        # of the specified cases (should be useful as a sanity check)
        context["non_case_facilities"] = facilities.exclude(case__in=cases)
        return context

    def render_to_response(self, context, **response_kwargs):
        if "download" in self.request.GET:
            # pypandoc will only write to disk. So, we make a temp file...
            with tempfile.NamedTemporaryFile() as fp:
                # ...write the converted document to it...
                pypandoc.convert_text(
                    context["letter_template"],
                    to="docx",
                    format="html",
                    outputfile=fp.name,
                )
                # ...and then read it into memory
                docx = fp.read()

            # Generate the filename based on the case number(s)
            case_nums = [str(c.case_num) for c in context["cases"]]
            filename = f"{'_'.join(case_nums)}_letter.docx"

            # And serve the document
            # TODO: Large files will probably cause issues here... will need to set up streaming if
            # this happens
            response = HttpResponse(
                docx,
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            response["Content-Disposition"] = f'application; filename="{filename}"'
            return response
        else:
            return super(LetterView, self).render_to_response(
                context, **response_kwargs
            )


class PreliminaryCaseGroupDetailView(DetailView):
    model = PreliminaryCaseGroup

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prelim_case_filter = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Prelim case table
        if self.prelim_case_filter is None:
            self.prelim_case_filter = PreliminaryCaseFilter(
                self.request.GET,
                queryset=PreliminaryCase.objects.filter(pcase_group=self.object),
                form_helper_kwargs={"form_class": "collapse"},
            )
            context["prelim_case_filter"] = self.prelim_case_filter

        if "prelim_case_table" not in context:
            table = PreliminaryCaseTable(data=self.prelim_case_filter.qs)
            table.paginate(page=self.request.GET.get("page", 1), per_page=10)
            context["prelim_case_table"] = table

        return context


class PreliminaryCaseDetailView(DetailView):
    model = PreliminaryCase

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attachment_filter = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["status_info"] = ["completed", "completed_on"]

        context["application_info"] = ["radio_service", "num_freqs", "num_sites"]

        if not self.attachment_filter:
            self.attachment_filter = AttachmentFilter(
                self.request.GET,
                queryset=self.object.attachments.all(),
                form_helper_kwargs={"form_class": "collapse"},
            )
            context["attachment_filter"] = self.attachment_filter

        if "attachment_table" not in context:
            table = AttachmentTable(data=self.attachment_filter.qs)
            table.paginate(page=self.request.GET.get("page", 1), per_page=10)
            context["attachment_table"] = table

        return context


class CaseDetailView(DetailView):
    model = Case

    def __init__(self, *args, **kwargs):
        super(CaseDetailView, self).__init__(*args, **kwargs)
        self.facility_filter = None
        self.attachment_filter = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["status_info"] = [
            "completed",
            "shutdown",
            "completed_on",
            "sgrs_notify",
            "sgrs_notified_on",
            "si_waived",
            "si",
            "si_done",
        ]

        context["application_info"] = [
            "radio_service",
            "call_sign",
            "freq_coord",
            "fcc_file_num",
            "num_freqs",
            "num_sites",
            "num_outside",
            "erpd_limit",
        ]

        if not self.facility_filter:
            self.facility_filter = FacilityFilter(
                self.request.GET,
                queryset=self.object.facilities.all(),
                form_helper_kwargs={"form_class": "collapse"},
            )
            context["facility_filter"] = self.facility_filter

        if "facility_table" not in context:
            table = FacilityTableWithConcur(data=self.facility_filter.qs)
            table.paginate(page=self.request.GET.get("page", 1), per_page=10)
            context["facility_table"] = table

        if not self.attachment_filter:
            self.attachment_filter = AttachmentFilter(
                self.request.GET,
                queryset=self.object.attachments.all(),
                form_helper_kwargs={"form_class": "collapse"},
            )
            context["attachment_filter"] = self.attachment_filter

        if "attachment_table" not in context:
            table = AttachmentTable(data=self.attachment_filter.qs)
            table.paginate(page=self.request.GET.get("page", 1), per_page=10)
            context["attachment_table"] = table

        return context

    def as_kml(self):
        case_as_kml(self.object)


class FacilityDetailView(DetailView):
    model = Facility

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meta_info"] = ["id", "created_on", "modified_on"]

        context["location_info"] = ["latitude", "longitude", "amsl", "agl"]
        context["antenna_info"] = [
            "freq_low",
            "freq_high",
            "bandwidth",
            "max_output",
            "antenna_gain",
            "system_loss",
            "main_beam_orientation",
            "mechanical_downtilt",
            "electrical_downtilt",
            "antenna_model_number",
        ]

        context["cell_info"] = [
            "tx_per_sector",
            "tx_antennas_per_sector",
            "technology",
            "uses_split_sectorization",
            "uses_cross_polarization",
            "num_quad_or_octal_ports_with_feed_power",
            "tx_power_pos_45",
            "tx_power_neg_45",
        ]

        context["other_info"] = ["site_name", "call_sign", "fcc_file_number"]

        return context

    def as_kml(self):
        facility_as_kml(self.object)


class AttachmentListView(FilterTableView):
    table_class = AttachmentTable
    filterset_class = AttachmentFilter
    template_name = "cases/attachment_list.html"


class AttachmentDetailView(DetailView):
    model = Attachment

    def __init__(self, *args, **kwargs):
        super(AttachmentDetailView, self).__init__(*args, **kwargs)
        self.case_filter = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meta_info"] = ["id", "created_on", "modified_on"]

        if self.case_filter is None:
            self.case_filter = CaseFilter(
                self.request.GET,
                queryset=self.object.cases.all(),
                form_helper_kwargs={"form_class": "collapse"},
            )
            context["case_filter"] = self.case_filter

        if "case_table" not in context:
            table = CaseTable(data=self.case_filter.qs)
            table.paginate(page=self.request.GET.get("page", 1), per_page=10)
            context["case_table"] = table

        return context


class PersonListView(FilterTableView):
    table_class = PersonTable
    filterset_class = PersonFilter
    template_name = "cases/person_list.html"


class PersonDetailView(DetailView):
    model = Person

    def __init__(self, *args, **kwargs):
        super(PersonDetailView, self).__init__(*args, **kwargs)
        self.case_filter = None
        self.prelim_case_filter = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["applicant_info"] = [
            # "cases",
            "name",
            "phone",
            "fax",
            "email",
            "street",
            "city",
            "county",
            "state",
            "zipcode",
        ]

        # Case table
        if self.case_filter is None:
            self.case_filter = CaseFilter(
                self.request.GET,
                queryset=Case.objects.filter(
                    Q(applicant=self.object) | Q(contact=self.object)
                ),
                form_helper_kwargs={"form_class": "collapse"},
            )
            context["case_filter"] = self.case_filter

        if "case_table" not in context:
            table = CaseTable(data=self.case_filter.qs)
            table.paginate(page=self.request.GET.get("page", 1), per_page=10)
            context["case_table"] = table

        # Prelim case table
        if self.prelim_case_filter is None:
            self.prelim_case_filter = PreliminaryCaseFilter(
                self.request.GET,
                queryset=PreliminaryCase.objects.filter(
                    Q(applicant=self.object) | Q(contact=self.object)
                ),
                form_helper_kwargs={"form_class": "collapse"},
            )
            context["prelim_case_filter"] = self.prelim_case_filter

        if "prelim_case_table" not in context:
            table = PreliminaryCaseTable(data=self.prelim_case_filter.qs)
            table.paginate(page=self.request.GET.get("page", 1), per_page=10)
            context["prelim_case_table"] = table

        return context


class StructureListView(FilterTableView):
    table_class = StructureTable
    filterset_class = StructureFilter
    template_name = "cases/structure_list.html"


class StructureDetailView(DetailView):
    model = Structure

    def __init__(self, *args, **kwargs):
        super(StructureDetailView, self).__init__(*args, **kwargs)
        self.facility_filter = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["info"] = [
            "asr",
            "file_num",
            "location",
            "faa_circ_num",
            "faa_study_num",
            "issue_date",
            "height",
        ]

        if not self.facility_filter:
            self.facility_filter = FacilityFilter(
                self.request.GET,
                queryset=self.object.facilities.all(),
                form_helper_kwargs={"form_class": "collapse"},
            )
            context["facility_filter"] = self.facility_filter

        if "facility_table" not in context:
            table = FacilityTable(data=self.facility_filter.qs)
            table.paginate(page=self.request.GET.get("page", 1), per_page=10)
            context["facility_table"] = table

        return context
