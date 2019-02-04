from datetime import date
import tempfile

from django.contrib.postgres.search import SearchVector
from django.db.models import Min, Max
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import Template, Context
from django.urls import reverse
from django.views.generic import FormView
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from docxtpl import DocxTemplate
from dal import autocomplete
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin
from django_tables2.export.views import ExportMixin
from django_tables2.export.export import TableExport

from .forms import LetterTemplateForm
from .models import (
    Attachment,
    PreliminaryCase,
    Case,
    PreliminaryFacility,
    Facility,
    Person,
    LetterTemplate,
    Structure,
    PreliminaryCaseGroup,
)
from .filters import (
    AttachmentFilter,
    FacilityFilter,
    PreliminaryFacilityFilter,
    PersonFilter,
    PreliminaryCaseGroupFilter,
    PreliminaryCaseFilter,
    CaseFilter,
    StructureFilter,
)
from .tables import (
    AttachmentTable,
    CaseExportTable,
    CaseTable,
    FacilityExportTable,
    FacilityTable,
    FacilityTableWithConcur,
    LetterFacilityTable,
    PersonTable,
    PreliminaryCaseGroupTable,
    PreliminaryCaseTable,
    PreliminaryFacilityTable,
    StructureTable,
)
from .kml import (
    facility_as_kml,
    facilities_as_kml,
    case_as_kml,
    cases_as_kml,
    kml_to_string,
)


class PrintableDetailView(DetailView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.path.endswith("print"):
            context["print"] = True

        return context


class FilterTableView(ExportMixin, SingleTableMixin, FilterView):
    table_class = None
    filterset_class = None
    object_list = NotImplemented
    export_table_class = None

    def get(self, request, *args, **kwargs):
        if "show-all" in request.GET:
            self.table_pagination = False

        self.export_requested = "_export" in request.GET
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # If there are no query params, then no results are
        # displayed -- but that's not what we want!
        if not self.request.GET:
            # Need this here to avoid a blank table appearing on first load
            self.object_list = self.table_class.Meta.model.objects.all()

        return super().get_context_data(**kwargs)

    def get_table_class(self, **kwargs):
        # If an export has been requested, AND we have a specific table
        # defined for export use, then return that
        if self.export_requested and self.export_table_class:
            return self.export_table_class
        # Otherwise, just act as normal
        else:
            return super().get_table_class(**kwargs)


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
    export_table_class = CaseExportTable
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


class PreliminaryFacilityListView(FilterTableView):
    table_class = PreliminaryFacilityTable
    filterset_class = PreliminaryFacilityFilter
    template_name = "cases/prelim_facility_list.html"


class FacilityListView(FilterTableView):
    table_class = FacilityTable
    filterset_class = FacilityFilter
    template_name = "cases/facility_list.html"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.annotate(calc_az=Azimuth(F("location"), gbt))

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
            facilities.filter(nrqz_id__isnull=False).values_list("nrqz_id", flat=True)
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

        context["letter_context"] = letter_context

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
            # context["letter_template"] = Template(letter_template.template).render(
            #     Context(letter_context)
            # )
            context["letter_template"] = letter_template.path
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
            dt = DocxTemplate(context["letter_template"])
            with tempfile.NamedTemporaryFile() as fp:
                dt.render(context["letter_context"])
                # ...write the converted document to it...
                # ...and then read it into memory
                dt.save(fp.name)
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


class PreliminaryCaseGroupDetailView(PrintableDetailView):
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


class PreliminaryCaseDetailView(PrintableDetailView):
    model = PreliminaryCase

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attachment_filter = None
        self.pfacility_filter = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["status_info"] = ["completed", "completed_on"]

        context["application_info"] = ["radio_service", "num_freqs", "num_sites"]

        if not self.pfacility_filter:
            self.pfacility_filter = PreliminaryFacilityFilter(
                self.request.GET,
                queryset=self.object.pfacilities.all(),
                form_helper_kwargs={"form_class": "collapse"},
            )
            context["pfacility_filter"] = self.pfacility_filter

        if "pfacility_table" not in context:
            table = PreliminaryFacilityTable(data=self.pfacility_filter.qs)
            table.paginate(page=self.request.GET.get("page", 1), per_page=10)
            context["pfacility_table"] = table

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


class CaseDetailView(PrintableDetailView):
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
            "si_waived",
            "si",
            "si_done",
            "name",
            "is_federal",
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
        context["sgrs_info"] = ["sgrs_notify", "sgrs_responded_on", "sgrs_service_num"]

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


class PreliminaryFacilityDetailView(PrintableDetailView):
    model = PreliminaryFacility

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meta_info"] = ["id", "created_on", "modified_on"]

        context["location_info"] = ["latitude", "longitude", "amsl", "agl"]
        context["antenna_info"] = ["freq_low", "antenna_model_number"]

        context["other_info"] = ["site_num", "site_name"]

        return context


class FacilityDetailView(PrintableDetailView):
    model = Facility

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meta_info"] = ["id", "created_on", "modified_on"]

        context["unsorted_info1"] = [
            "asr_is_from_applicant",
            "band_allowance",
            "distance_to_first_obstacle",
            "dominant_path",
            "erpd_per_num_tx",
            "height_of_first_obstacle",
            "loc",
        ]
        context["unsorted_info2"] = [
            "max_aerpd",
            "max_erp_per_tx",
            "max_gain",
            "max_tx_power",
            "nrao_aerpd",
            "power_density_limit",
            "sgrs_approval",
            "tap_file",
        ]
        context["unsorted_info3"] = [
            "tap",
            "tx_power",
            "aeirp_to_gbt",
            "az_bearing",
            "calc_az",
            "num_tx_per_facility",
            "nrao_approval",
        ]
        context["location_info"] = ["location", "amsl", "agl"]
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
            "uses_quad_or_octal_polarization",
            "num_quad_or_octal_ports_with_feed_power",
            "tx_power_pos_45",
            "tx_power_neg_45",
        ]

        context["other_info"] = [
            "site_num",
            "site_name",
            "call_sign",
            "fcc_file_number",
        ]

        return context

    def as_kml(self):
        facility_as_kml(self.object)


class AttachmentListView(FilterTableView):
    table_class = AttachmentTable
    filterset_class = AttachmentFilter
    template_name = "cases/attachment_list.html"


class AttachmentDetailView(PrintableDetailView):
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


class PersonDetailView(PrintableDetailView):
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


class StructureDetailView(PrintableDetailView):
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


class SearchView(SingleTableMixin, ListView):
    table_class = CaseTable
    template_name = "cases/search_results.html"

    def search(self, query):
        self.searched_by_case_num = False

        try:
            case_qs_from_case_num = Case.objects.filter(case_num=query)
            if case_qs_from_case_num.exists():
                self.searched_by_case_num = True
                return case_qs_from_case_num.all()
        except ValueError:
            pass

        # print("No exact match by case number; continuing to full text search")
        return Case.objects.annotate(
            search=SearchVector("applicant__name", "contact__name", "comments")
        ).filter(search=query)

    def get_context_data(self, **kwargs):
        kwargs["searched_by_case_num"] = self.searched_by_case_num
        kwargs["query"] = self.query
        return super().get_context_data(**kwargs)

    def get(self, request, *args, **kwargs):
        # query = request.GET.get("q", None)
        # if query:
        #     cases = self.search(query)
        # else:
        #     cases = Case.objects.none()

        self.query = request.GET.get("q", None)

        self.object_list = self.get_queryset()
        if self.object_list.count() == 1:
            return HttpResponseRedirect(
                reverse("case_detail", args=[self.object_list.first().case_num])
            )
        context = self.get_context_data()
        return self.render_to_response(context)

    def get_queryset(self):
        if self.query:
            cases = self.search(self.query)
        else:
            cases = Case.objects.none()

        return cases


def search(request):
    return HttpResponse("yo")


def facility_as_kml_view(request, pk):
    facility = Facility.objects.get(id=pk)
    response = HttpResponse(
        facility.location.kml, content_type="application/vnd.google-earth.kml+xml."
    )
    response["Content-Disposition"] = f'application; filename="{facility.nrqz_id}.kml"'
    return response
