from datetime import date
import tempfile

from django.contrib import messages
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
    object_list = None
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

    def render_to_response(self, context, **response_kwargs):
        if "mass-edit" in self.request.GET and self.object_list:
            verbose_name_plural = (
                self.filterset_class.Meta.model._meta.verbose_name_plural
            )
            messages.info(
                self.request,
                f"Any changes made here will affect {verbose_name_plural}: "
                f"{self.object_list.all()}",
            )
            num_items = self.object_list.count()
            if num_items > 100:
                messages.warning(
                    self.request,
                    f"Are you sure you want to mass edit {num_items} {verbose_name_plural} (it's a lot...)?",
                )

            app = self.filterset_class.Meta.model._meta.app_label
            model = self.filterset_class.Meta.model.__name__.lower()
            instances = ",".join(
                str(item) for item in self.object_list.values_list("id", flat=True)
            )
            return HttpResponseRedirect(
                reverse("massadmin_change_view", args=[app, model, instances])
            )

        return super().render_to_response(context, **response_kwargs)


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


class LetterView(FormView):
    form_class = LetterTemplateForm
    template_name = "cases/concurrence_letter.html"

    # def get_success_url(self):
    #     return reverse("letters")

    # def get(self, request, *args, **kwargs):
    #     print("GET")
    #     facilities_q = Q()
    #     if "facilities" in request.GET:
    #         kwargs.update({"facilities": request.GET.getlist("facilities")})
    #         facilities_q |= Q(id__in=request.GET.getlist("facilities"))

    #     if "cases" in request.GET:
    #         kwargs.update({"cases": request.GET.getlist("cases")})
    #         facilities_q |= Q(case__case_num__in=request.GET.getlist("cases"))

    #     if "template" in request.GET:
    #         kwargs.update({"template": request.GET["template"]})

    #     if facilities_q:
    #         facilities = Facility.objects.filter(facilities_q)
    #     else:
    #         facilities = Facility.objects.none()
    #     kwargs.update({"facilities_result": facilities})
    #     print("KWARGS", kwargs)
    #     return super().get(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if "facilities" in self.request.GET:
            initial.update({"facilities": self.request.GET.getlist("facilities")})

        if "cases" in self.request.GET:
            initial.update({"cases": self.request.GET.getlist("cases")})

        if "template" in self.request.GET:
            initial.update({"template": self.request.GET["template"]})

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_letter_context(self.request.GET))
        return context

    def get_letter_context(self, post_dict):
        if "facilities" in post_dict:
            facilities = Facility.objects.filter(id__in=post_dict.getlist("facilities"))
            cases = Case.objects.filter(facilities__in=facilities)
        else:
            if "cases" in post_dict:
                cases = Case.objects.filter(case_num__in=post_dict.getlist("cases"))
                cases = (
                    cases | Case.objects.filter(facilities__in=facilities)
                ).distinct()
            else:
                raise ValueError("At least one of cases or facilities must be here...")

        if cases.count() != 1:
            raise ValueError("Womp womp")

        case = cases.first()

        letter_context = {"case": case, "facilities": facilities}

        letter_context["generation_date"] = date.today().strftime("%B %d, %Y")
        letter_context["nrqz_ids"] = ", ".join(
            facilities.filter(nrqz_id__isnull=False).values_list("nrqz_id", flat=True)
        )
        table = LetterFacilityTable(data=facilities)
        letter_context["facilities_table"] = table

        return letter_context

    def render_to_response(self, context, **response_kwargs):
        if "download" in self.request.GET:
            # We make a temp file...
            letter_context = self.get_letter_context(self.request.GET)
            letter_template = get_object_or_404(
                LetterTemplate, path__endswith=self.request.GET.get("template", None)
            )
            dt = DocxTemplate(letter_template.path)
            with tempfile.NamedTemporaryFile() as fp:
                dt.render(letter_context)
                # ...write the converted document to it...
                dt.save(fp.name)
                # ...and then read it into memory
                docx = fp.read()

            # Generate the filename based on the case number(s)
            filename = f"{letter_context['case'].case_num}_letter.docx"

            # And serve the document
            # TODO: Large files will probably cause issues here... will need to set up streaming if
            # this happens
            response = HttpResponse(
                docx,
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            response["Content-Disposition"] = f'application; filename="{filename}"'
            return response

        return super().render_to_response(context, **response_kwargs)


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
        # context["meta_info"] = ["id", "created_on", "modified_on"]
        context["topography_info"] = [
            "site_name",
            # geographic location,
            # lat
            # long
            "location",
            # nad88 nad83 nad27
            "amsl",
            # survey 1a/2a
        ]
        context["antenna_info"] = [
            "agl",
            "antenna_model_number",
            "antenna_gain",
            # az deg true
            "main_beam_orientation",
            "mechanical_downtilt",
            "electrical_downtilt",
        ]

        # TODO
        # context["path_data_info"] [

        # ]
        # TODO:
        # context["usgs_dataset_info"]

        context["transmitter_info"] = [
            "freq_low",
            "freq_high",
            "power_density_limit",
            "tx_per_sector",
            "max_tx_power",
            "num_tx_per_facility",
            "max_erp_per_tx",
        ]

        context["emissions_info"] = ["bandwidth"]

        context["path_attenuation_info"] = [
            # diffraction
            # troposcatter
            # free space
            "tpa",
            # "attachments" prop study
            "calc_az",
            "distance_to_first_obstacle",
            "height_of_first_obstacle",
            "dominant_path",
        ]

        context["analysis_results_info"] = [
            # TODO: Check
            # ERPd Restriction True/False
            # "erpd_limit",
            # analog AERPd
            # CDMA AERPd
            # CDMA 2000 AERPd
            # GSM AERPd
            # Emission AERPd
        ]
        context["federal_info"] = [
            # "case.is_federal",
            # "sgrs367"
        ]

        context["sgrs_info"] = [
            "sgrs_approval"
            # TODO
            # date
        ]

        known_fields = [
            value
            for info_key, info_list in context.items()
            if isinstance(info_list, list)
            for value in info_list
            if info_key.endswith("info")
        ]
        context["unsorted_info"] = sorted(
            f[0] for f in self.object.all_fields() if f[0] not in known_fields
        )
        # "max_output",
        # "system_loss",
        # "main_beam_orientation",
        # context["unsorted_info1"] = [
        #     "asr_is_from_applicant",
        #     "band_allowance",
        #     "erpd_per_num_tx",
        #     "loc",
        # ]
        # context["unsorted_info2"] = [
        #     "max_aerpd",
        #     "max_gain",
        #     "nrao_aerpd",
        #     "sgrs_approval",
        #     "tap_file",
        # ]
        # context["unsorted_info3"] = [
        #     "tx_power",
        #     "aeirp_to_gbt",
        #     "az_bearing",
        #     "nrao_approval",
        # ]

        # context["cell_info"] = [
        #     "tx_antennas_per_sector",
        #     "technology",
        #     "uses_split_sectorization",
        #     "uses_cross_polarization",
        #     "uses_quad_or_octal_polarization",
        #     "num_quad_or_octal_ports_with_feed_power",
        #     "tx_power_pos_45",
        #     "tx_power_neg_45",
        # ]

        # context["other_info"] = ["site_num", "call_sign", "fcc_file_number"]

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
