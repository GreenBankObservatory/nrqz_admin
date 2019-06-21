from datetime import date
import tempfile

from docxtpl import DocxTemplate

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.search import SearchVector
from django.db import transaction
from django.db.models import (
    Count,
    Case as CASE,
    Value,
    F,
    Q,
    BooleanField,
    When,
    Min,
    Max,
    Q,
    Count,
)
from django.db.utils import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import Template, Context
from django.urls import reverse
from django.views.generic import FormView
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from django_filters.views import FilterView
from django_tables2.export.export import TableExport
from django_tables2.export.views import ExportMixin
from django_tables2.views import SingleTableMixin, MultiTableMixin
from watson import search as watson

from utils.coord_utils import coords_to_string
from utils.merge_people import find_similar_people, merge_people
from .forms import LetterTemplateForm, DuplicateCaseForm
from .models import (
    Attachment,
    Case,
    CaseGroup,
    Facility,
    LetterTemplate,
    Person,
    PreliminaryCase,
    PreliminaryCaseGroup,
    PreliminaryFacility,
    Structure,
)
from .filters import (
    AttachmentFilter,
    CaseFilter,
    CaseGroupFilter,
    FacilityFilter,
    PersonFilter,
    PreliminaryCaseFilter,
    PreliminaryCaseGroupFilter,
    PreliminaryFacilityFilter,
    StructureFilter,
)
from .tables import (
    AttachmentTable,
    CaseExportTable,
    CaseGroupTable,
    CaseTable,
    FacilityExportTable,
    FacilityTable,
    FacilityTableWithConcur,
    LetterFacilityTable,
    PersonTable,
    PreliminaryCaseExportTable,
    PreliminaryCaseGroupTable,
    PreliminaryCaseTable,
    PreliminaryFacilityExportTable,
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

        if "csv" in request.GET.get("_export", ""):
            self.export_requested = True
            # Change the value to csv so that django-tables2 understands the
            # export request
            request.GET = request.GET.copy()
            request.GET["_export"] = "csv"
        else:
            self.export_requested = False

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


class CaseGroupDetailView(MultiTableMixin, DetailView):
    model = CaseGroup
    tables = [CaseTable]
    table_pagination = {"per_page": 10}

    def get_tables_data(self):
        case_filter_qs = CaseFilter(
            self.request.GET,
            queryset=self.object.cases.all(),
            form_helper_kwargs={"form_class": "collapse"},
        ).qs
        return [case_filter_qs]


class CaseGroupListView(FilterTableView):
    table_class = CaseGroupTable
    filterset_class = CaseGroupFilter
    template_name = "cases/case_group_list.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(num_cases=Count("cases"))
        return queryset


class PreliminaryCaseGroupListView(FilterTableView):
    table_class = PreliminaryCaseGroupTable
    filterset_class = PreliminaryCaseGroupFilter
    template_name = "cases/prelim_case_group_list.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(num_pcases=Count("prelim_cases"))
        return queryset


class PreliminaryCaseListView(FilterTableView):
    table_class = PreliminaryCaseTable
    filterset_class = PreliminaryCaseFilter
    export_table_class = PreliminaryCaseExportTable
    template_name = "cases/prelim_case_list.html"


class CaseListView(FilterTableView):
    table_class = CaseTable
    export_table_class = CaseExportTable
    filterset_class = CaseFilter
    template_name = "cases/case_list.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(
            num_facilities=Count("facilities"),
            sgrs_pending=Count("id", filter=Q(facilities__sgrs_approval=None)),
            sgrs_approvals=Count("id", filter=Q(facilities__sgrs_approval=True)),
        )
        queryset = queryset.annotate(
            sgrs_approval=CASE(
                When(sgrs_pending__gt=0, then=Value(None)),
                When(sgrs_approvals=F("num_facilities"), then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        queryset = queryset.annotate(
            num_facilities=Count("facilities"),
            erpd_limit_pending=Count("id", filter=Q(facilities__meets_erpd_limit=None)),
            erpd_limit_pass=Count("id", filter=Q(facilities__meets_erpd_limit=True)),
        )
        queryset = queryset.annotate(
            meets_erpd_limit=CASE(
                When(erpd_limit_pending__gt=0, then=Value(None)),
                When(erpd_limit_pass=F("num_facilities"), then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        queryset = queryset.annotate(num_facilities=Count("facilities"))
        queryset = queryset.annotate(si_done=Max("facilities__si_done"))
        return queryset

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
    export_table_class = PreliminaryFacilityExportTable
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


class PreliminaryCaseGroupDetailView(MultiTableMixin, DetailView):
    model = PreliminaryCaseGroup
    tables = [PreliminaryCaseTable]
    table_pagination = {"per_page": 10}

    def get_tables_data(self):
        pcase_filter_qs = PreliminaryCaseFilter(
            self.request.GET,
            queryset=self.object.prelim_cases.all(),
            form_helper_kwargs={"form_class": "collapse"},
        ).qs
        return [pcase_filter_qs]


class PreliminaryCaseDetailView(MultiTableMixin, DetailView):
    model = PreliminaryCase
    tables = [PreliminaryFacilityTable, AttachmentTable, PreliminaryCaseTable]
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
        pcase_filter_qs = PreliminaryCaseFilter(
            self.request.GET,
            queryset=self.object.related_prelim_cases,
            form_helper_kwargs={"form_class": "collapse"},
        ).qs
        return [pfacility_filter_qs, attachment_filter_qs, pcase_filter_qs]

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
    tables = [FacilityTable, AttachmentTable, CaseTable, PreliminaryCaseTable]
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

        case_filter_qs = CaseFilter(
            self.request.GET,
            queryset=self.object.related_cases,
            form_helper_kwargs={"form_class": "collapse"},
        ).qs

        pcase_filter_qs = PreliminaryCaseFilter(
            self.request.GET,
            queryset=self.object.related_prelim_cases,
            form_helper_kwargs={"form_class": "collapse"},
        ).qs

        return [
            facility_filter_qs,
            attachment_filter_qs,
            case_filter_qs,
            pcase_filter_qs,
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        si_done = self.object.get_si_done()
        context["status_info"] = [
            "shutdown",
            (
                "Completed On",
                self.object.completed_on.date() if self.object.completed_on else None,
                "",
            ),
            "si_waived",
            "si",
            ("SI Done", si_done.date() if si_done else None, ""),
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
            ("Meets ERPd Limit", self.object.get_meets_erpd_limit, ""),
        ]
        context["sgrs_info"] = [
            "sgrs_notify",
            (
                "SGRS Responded On",
                self.object.sgrs_responded_on.date()
                if self.object.sgrs_responded_on
                else None,
                "",
            ),
            "sgrs_service_num",
            ("SGRS Approval", self.object.get_sgrs_approval, ""),
        ]
        context["unsorted_info"] = get_fields_missing_from_info_tables(
            context, self.object.all_fields()
        )
        context["duplicate_case_form"] = DuplicateCaseForm()
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

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context["status_info"] = ["completed_on"]
    #     context["application_info"] = ["radio_service", "num_freqs", "num_sites"]
    #     context["unsorted_info"] = get_fields_missing_from_info_tables(
    #         context, self.object.all_fields()
    #     )
    #     return context


class PersonDetailView(MultiTableMixin, DetailView):
    tables = [CaseTable, PreliminaryCaseTable, PersonTable]
    model = Person
    table_pagination = {"per_page": 10}

    def get_tables_data(self):
        case_filter_qs = CaseFilter(
            self.request.GET,
            queryset=Case.objects.filter(
                Q(applicant=self.object) | Q(contact=self.object)
            ),
            form_helper_kwargs={"form_class": "collapse"},
        ).qs
        pcase_filter_qs = PreliminaryCaseFilter(
            self.request.GET,
            queryset=PreliminaryCase.objects.filter(
                Q(applicant=self.object) | Q(contact=self.object)
            ),
            form_helper_kwargs={"form_class": "collapse"},
        ).qs
        person_filter_qs = PersonFilter(
            self.request.GET,
            queryset=find_similar_people(self.object),
            form_helper_kwargs={"form_class": "collapse"},
        ).qs
        return [case_filter_qs, pcase_filter_qs, person_filter_qs]

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

        return context


def merge_similar_people(request, pk):
    """Given a Person ID, find people similar to them and merge them all together

    Person with given ID will be kept; others will be merged
    """

    person = get_object_or_404(Person, id=pk)
    similar_people = find_similar_people(person).exclude(id=person.id)
    if similar_people:
        with transaction.atomic():
            merge_people(person_to_keep=person, people_to_merge=similar_people)
        messages.success(
            request,
            f"Successfully merged {person.merge_info.num_instances_merged - 1} "
            f"people into {person.name}",
        )
    else:
        messages.warning(request, f"There are no similar people to merge!")
    return HttpResponseRedirect(person.get_absolute_url())


class StructureListView(FilterTableView):
    table_class = StructureTable
    filterset_class = StructureFilter
    template_name = "cases/structure_list.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(
            num_facilities=Count("facilities"),
            num_cases=Count("facilities__case", distinct=True),
        )
        return queryset


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
            (
                "Location",
                coords_to_string(
                    latitude=self.object.location.y,
                    longitude=self.object.location.x,
                    concise=True,
                ),
                "",
            ),
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


@transaction.atomic
def duplicate_case(request, case_num):
    case = get_object_or_404(Case, case_num=case_num)
    num_duplicates = int(request.POST.get("num_duplicates"))

    successful_duplications = []
    failed_duplications = []
    for __ in range(num_duplicates):
        case.id = None
        case.case_num += 1
        try:
            with transaction.atomic():
                case.save()
        except IntegrityError as error:
            if "duplicate" in error.args[0]:
                failed_duplications.append(case.case_num)
            else:
                raise
        else:
            successful_duplications.append(case.case_num)

    if failed_duplications:
        transaction.set_rollback(True)
        if len(failed_duplications) > 1:
            message_text = (
                f"Cases {failed_duplications} already exist! No new cases created"
            )
        elif len(failed_duplications) == 1:
            message_text = (
                f"Case {failed_duplications[0]} already exists! No new case created"
            )
        else:
            raise ValueError("This shouldn't be possible...")

        messages.error(request, message_text)
        return HttpResponseRedirect(reverse("case_detail", args=[case_num]))

    if len(successful_duplications) > 1:
        message_text = f"Cases {successful_duplications} have been successfully duplicated from case {case_num}!"

    elif len(successful_duplications) == 1:
        message_text = f"Case {successful_duplications[0]} has been successfully duplicated from case {case_num}!"

    else:
        raise ValueError("This shouldn't be possible...")

    messages.success(request, message_text)
    return HttpResponseRedirect(reverse("case_detail", args=[case.case_num]))
