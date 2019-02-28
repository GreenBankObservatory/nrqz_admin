from datetime import date
import tempfile

from docxtpl import DocxTemplate

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
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

from dal import autocomplete
from django_filters.views import FilterView
from django_tables2.export.export import TableExport
from django_tables2.export.views import ExportMixin
from django_tables2.views import SingleTableMixin, MultiTableMixin
from watson import search as watson

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
    SearchEntryTable,
    StructureTable,
)
from .kml import (
    facility_as_kml,
    facilities_as_kml,
    case_as_kml,
    cases_as_kml,
    kml_to_string,
)


def get_fields_missing_from_info_tables(context, all_model_fields):
    known_fields = [
        value
        for info_key, info_list in context.items()
        if isinstance(info_list, list)
        for value in info_list
        if info_key.endswith("info")
    ]
    return sorted(f[0] for f in all_model_fields if f[0] not in known_fields)


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

    def get_queryset(self):
        return self.table_class.Meta.model.objects.all()

    def get_context_data(self, **kwargs):
        # If there are no query params, then no results are
        # displayed -- but that's not what we want!
        if not self.request.GET:
            # Need this here to avoid a blank table appearing on first load
            self.object_list = self.get_queryset()

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
                kml_to_string(
                    cases_as_kml(qs.filter(facility__location__isnull=False).all())
                ),
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

    def get_queryset(self):
        return (
            PreliminaryFacility.objects.annotate_in_nrqz()
            .annotate_azimuth_to_gbt()
            .annotate_distance_to_gbt()
        )


class FacilityListView(FilterTableView):
    table_class = FacilityTable
    filterset_class = FacilityFilter
    export_table_class = FacilityExportTable
    template_name = "cases/facility_list.html"

    def get_queryset(self):
        return (
            Facility.objects.annotate_in_nrqz()
            .annotate_azimuth_to_gbt()
            .annotate_distance_to_gbt()
        )

    def get(self, request, *args, **kwargs):
        if "kml" in request.GET:
            # TODO: Must be a cleaner way to do this
            qs = self.get_filterset(self.filterset_class).qs
            response = HttpResponse(
                kml_to_string(
                    facilities_as_kml(qs.filter(location__isnull=False).all())
                ),
                content_type="application/vnd.google-earth.kml+xml.",
            )
            response[
                "Content-Disposition"
            ] = 'application; filename="nrqz_facilities.kml"'
            return response
        else:
            return super(FacilityListView, self).get(request, *args, **kwargs)


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


class LetterView(FormView):
    form_class = LetterTemplateForm
    template_name = "cases/concurrence_letter.html"

    def get_initial(self):
        initial = super().get_initial()
        if "facilities" in self.request.GET:
            initial.update({"facilities": self.request.GET.getlist("facilities")})

        if "cases" in self.request.GET:
            initial.update({"cases": self.request.GET.getlist("cases")})

        if "template" in self.request.GET:
            initial.update({"template": self.request.GET["template"]})

        return initial

    def get_letter_context(self, post_dict):
        cases = post_dict["cases"]
        facilities = post_dict["facilities"]

        if cases.count() != 1:
            raise ValueError(
                f"There should only be one unique case! Got {cases.count()}!"
            )

        case = cases.first()

        letter_context = {"case": case, "facilities": facilities}

        letter_context["generation_date"] = date.today().strftime("%B %d, %Y")
        letter_context["nrqz_ids"] = ", ".join(
            facilities.filter(nrqz_id__isnull=False).values_list("nrqz_id", flat=True)
        )
        table = LetterFacilityTable(data=facilities)
        letter_context["facilities_table"] = table

        return letter_context

    def form_valid(self, form):
        # We make a temp file...
        letter_context = self.get_letter_context(form.cleaned_data)
        letter_template = form.cleaned_data["template"]
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


class PreliminaryCaseDetailView(MultiTableMixin, DetailView):
    model = PreliminaryCase
    tables = [PreliminaryFacilityTable, AttachmentTable]
    table_pagination = {"per_page": 10}

    def get_tables_data(self):
        pfacility_filter_qs = PreliminaryFacilityFilter(
            self.request.GET,
            queryset=self.object.pfacilities.all(),
            form_helper_kwargs={"form_class": "collapse"},
        ).qs
        attachment_filter_qs = AttachmentFilter(
            self.request.GET,
            queryset=self.object.attachments.all(),
            form_helper_kwargs={"form_class": "collapse"},
        ).qs
        return [pfacility_filter_qs, attachment_filter_qs]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_info"] = ["completed_on"]
        context["application_info"] = ["radio_service", "num_freqs", "num_sites"]
        context["unsorted_info"] = get_fields_missing_from_info_tables(
            context, self.object.all_fields()
        )
        return context


class CaseDetailView(MultiTableMixin, DetailView):
    model = Case
    tables = [FacilityTable, AttachmentTable]
    table_pagination = {"per_page": 10}

    def get_tables_data(self):
        facility_filter_qs = FacilityFilter(
            self.request.GET,
            queryset=self.object.facilities.all(),
            form_helper_kwargs={"form_class": "collapse"},
        ).qs
        attachment_filter_qs = AttachmentFilter(
            self.request.GET,
            queryset=self.object.attachments.all(),
            form_helper_kwargs={"form_class": "collapse"},
        ).qs

        return [facility_filter_qs, attachment_filter_qs]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_info"] = [
            "shutdown",
            "completed_on",
            "si_waived",
            "si",
            "si_done",
            "is_federal",
        ]
        context["application_info"] = [
            "radio_service",
            "call_sign",
            "freq_coord",
            "fcc_file_num",
            "num_sites",
            "num_freqs",
            "num_outside",
            ("Meets ERPd Limit", self.object.meets_erpd_limit, ""),
        ]
        context["sgrs_info"] = [
            "sgrs_notify",
            "sgrs_responded_on",
            "sgrs_service_num",
            ("SGRS Approval", self.object.sgrs_approval, ""),
        ]
        context["unsorted_info"] = get_fields_missing_from_info_tables(
            context, self.object.all_fields()
        )
        return context

    def as_kml(self):
        case_as_kml(self.object)


class BaseFacilityDetailView(DetailView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["topography_info"] = [
            "site_name",
            "call_sign",
            "location_description",
            "location",
            "amsl",
            "survey_1a",
            "survey_2c",
            (
                "Inside NRQZ?",
                self.object.get_in_nrqz(),
                "Indicates whether the facility is inside the boundaries of the NRQZ",
            ),
        ]

        context["path_data_interpolation_info"] = [
            "topo_4_point",
            "topo_12_point",
            "propagation_model",
        ]
        # TODO:
        context["usgs_dataset_info"] = ["usgs_dataset"]

        context["emissions_info"] = ["bandwidth", "emissions"]

        context["path_attenuation_info"] = [
            "nrao_diff",
            "nrao_space",
            "nrao_tropo",
            "tpa",
            "distance_to_first_obstacle",
            "height_of_first_obstacle",
            "dominant_path",
            ("Propagation Study", self.object.get_prop_study_as_link(), ""),
        ]

        context["analysis_results_info"] = [
            "nrao_aerpd",
            "nrao_aerpd_analog",
            "nrao_aerpd_gsm",
            "nrao_aerpd_cdma",
            "nrao_aerpd_cdma2000",
        ]
        context["federal_info"] = [
            ("Is Federal?", self.object.case.is_federal, ""),
            "s367",
        ]

        context["sgrs_info"] = [
            "sgrs_approval"
            # TODO
            # date
        ]
        context["analysis_results_info"]

        return context


class PreliminaryFacilityDetailView(BaseFacilityDetailView):
    model = PreliminaryFacility

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["location_info"] = ["location", "amsl", "agl"]
        context["topography_info"] = [
            item for item in context["topography_info"] if item != "call_sign"
        ]
        context["antenna_info"] = [
            "agl",
            "antenna_model_number",
            (
                "Azimuth Bearing",
                f"{self.object.get_azimuth_to_gbt():.2f}°"
                if self.object.location
                else None,
                "Azimuth bearing to GBT in degrees",
            ),
        ]
        context["transmitter_info"] = [
            "freq_low",
            "freq_high",
            "power_density_limit",
            # "tx_per_sector",
            # "max_tx_power",
            # "num_tx_per_facility",
            # "max_erp_per_tx",
        ]
        context["unsorted_info"] = get_fields_missing_from_info_tables(
            context, self.object.all_fields()
        )
        return context


class FacilityDetailView(MultiTableMixin, BaseFacilityDetailView):
    model = Facility
    tables = [AttachmentTable]
    table_pagination = {"per_page": 10}

    def get_tables_data(self):
        attachment_filter_qs = AttachmentFilter(
            self.request.GET,
            queryset=self.object.attachments.all(),
            form_helper_kwargs={"form_class": "collapse"},
        ).qs
        return [attachment_filter_qs]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["antenna_info"] = [
            "agl",
            "antenna_model_number",
            "antenna_gain",
            (
                "Azimuth Bearing",
                self.object.get_azimuth_to_gbt() if self.object.location else None,
                "Azimuth bearing to GBT in degrees",
            ),
            # az deg true
            "main_beam_orientation",
            "mechanical_downtilt",
            "electrical_downtilt",
        ]
        context["transmitter_info"] = [
            "freq_low",
            "freq_high",
            "power_density_limit",
            "tx_per_sector",
            "max_tx_power",
            "num_tx_per_facility",
            "requested_max_erp_per_tx",
        ]
        context["unsorted_info"] = get_fields_missing_from_info_tables(
            context, self.object.all_fields()
        )

        context["analysis_results_info"] = [
            "meets_erpd_limit",
            *context["analysis_results_info"],
        ]
        return context

    def as_kml(self):
        facility_as_kml(self.object)


class AttachmentListView(FilterTableView):
    table_class = AttachmentTable
    filterset_class = AttachmentFilter
    template_name = "cases/attachment_list.html"


class AttachmentDetailView(MultiTableMixin, DetailView):
    model = Attachment
    tables = [CaseTable, PreliminaryCaseTable, FacilityTable, PreliminaryFacilityTable]
    table_pagination = {"per_page": 10}

    def get_tables_data(self):
        attachment = self.object
        return [
            table._meta.model.objects.filter(id__in=attachment.cases.values("id"))
            for table in self.tables
        ]

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context["tables_with_model_names"] = zip(
            [table._meta.model._meta.verbose_name for table in self.tables],
            context["tables"],
        )
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


class SearchView(MultiTableMixin, ListView):
    tables = [SearchEntryTable, SearchEntryTable, SearchEntryTable]
    table_pagination = {"per_page": 10}
    template_name = "cases/search_results.html"

    def get_tables_data(self):
        for table in self.tables:
            table.query = self.query

        data = [
            self.object_list.filter(
                content_type=ContentType.objects.get_for_model(model)
            )
            for model in [Case, Facility, Person]
        ]
        return data

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context["query"] = self.query
        context["tables_with_model_names"] = zip(
            ["Case", "Facility", "Person"], context["tables"]
        )
        return context

    def get(self, request, *args, **kwargs):
        self.query = request.GET.get("q", None)
        self.object_list = watson.search(self.query)
        context = self.get_context_data()
        return self.render_to_response(context)


def facility_as_kml_view(request, pk):
    facility = Facility.objects.get(id=pk)
    response = HttpResponse(
        facility.as_kml(), content_type="application/vnd.google-earth.kml+xml."
    )
    response["Content-Disposition"] = f'application; filename="{facility.nrqz_id}.kml"'
    return response


def case_as_kml_view(request, pk):
    case = Case.objects.get(id=pk)
    response = HttpResponse(
        case.as_kml(), content_type="application/vnd.google-earth.kml+xml."
    )
    response["Content-Disposition"] = f'application; filename="{case.case_num}.kml"'
    return response
