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
from .models import Attachment, Batch, Case, Facility, Person, LetterTemplate
from .filters import (
    AttachmentFilter,
    BatchFilter,
    FacilityFilter,
    PersonFilter,
    CaseFilter,
)
from .tables import (
    AttachmentTable,
    BatchTable,
    FacilityTable,
    PersonTable,
    CaseTable,
    ConcurrenceFacilityTable,
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
                self.request.GET, queryset=self.object.cases.all()
            )
            context["case_filter"] = self.case_filter

        if "case_table" not in context:
            table = CaseTable(data=self.case_filter.qs)
            table.paginate(page=self.request.GET.get("page", 1), per_page=10)
            context["case_table"] = table

        return context


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


class CaseAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        cases = Case.objects.order_by("case_num")
        if self.q:
            cases = cases.filter(case_num__istartswith=self.q).order_by("case_num")
        return cases


class FacilityAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        facilities = Facility.objects.order_by("nrqz_id")
        if self.q:
            facilities = facilities.filter(nrqz_id__icontains=self.q)
        return facilities




class ConcurrenceLetterView(TemplateView):
    template_name = "cases/concurrence_letter.html"

    def get(self, request, *args, **kwargs):
        facilities_q = Q()
        if "facilities" in request.GET:
            kwargs.update({"facilities": request.GET.getlist("facilities")})
            facilities_q |= Q(id__in=request.GET.getlist("facilities"))

        if "cases" in request.GET:
            kwargs.update({"cases": request.GET.getlist("cases")})
            facilities_q |= Q(case__in=request.GET.getlist("cases"))

        if "batches" in request.GET:
            kwargs.update({"batches": request.GET.getlist("batches")})
            facilities_q |= Q(batch__case__in=request.GET.getlist("batches"))

        if "template" in request.GET:
            kwargs.update({"template": request.GET["template"]})

        if facilities_q:
            facilities = Facility.objects.filter(facilities_q)
        else:
            facilities = Facility.objects.none()
        kwargs.update({"facilities_result": facilities})
        # print(facilities.count())

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        facilities = context["facilities_result"]
        if "cases" in context:
            cases = Case.objects.filter(id__in=context["cases"])
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
        table = ConcurrenceFacilityTable(data=facilities)
        letter_context["facilities_table"] = table

        if "template" in context:
            letter_template_text = get_object_or_404(
                LetterTemplate, name=context["template"]
            ).template
        else:
            try:
                letter_template_text = LetterTemplate.objects.get(
                    name="default"
                ).template
                kwargs["template"] = "default"
            except LetterTemplate.DoesNotExist:
                lt = LetterTemplate.objects.first()
                letter_template_text = lt.template
                kwargs["template"] = lt.name
        # import ipdb; ipdb.set_trace()
        # print(letter_template_text)
        form_values = {
            field: value
            for field, value in kwargs.items()
            if field in ["cases", "facilities", "batches", "template"]
        }
        print(f"form_values: {form_values}")
        context["template_form"] = LetterTemplateForm(form_values)
        context["letter_template"] = Template(letter_template_text).render(
            Context(letter_context)
        )
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
            return super(ConcurrenceLetterView, self).render_to_response(
                context, **response_kwargs
            )


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
            "fcc_freq_coord",
            "fcc_file_num",
            "num_freqs",
            "num_sites",
            "num_outside",
            "erpd_limit",
        ]

        if not self.facility_filter:
            self.facility_filter = FacilityFilter(
                self.request.GET, queryset=self.object.facilities.all()
            )
            context["facility_filter"] = self.facility_filter

        if "facility_table" not in context:
            table = FacilityTable(data=self.facility_filter.qs)
            table.paginate(page=self.request.GET.get("page", 1), per_page=10)
            context["facility_table"] = table

        if not self.attachment_filter:
            self.attachment_filter = AttachmentFilter(
                self.request.GET, queryset=self.object.attachments.all()
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
                self.request.GET, queryset=self.object.cases.all()
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

        if self.case_filter is None:
            self.case_filter = CaseFilter(
                self.request.GET, queryset=self.object.applicant_for_cases.all()
            )
            context["case_filter"] = self.case_filter

        if "case_table" not in context:
            table = CaseTable(data=self.case_filter.qs)
            table.paginate(page=self.request.GET.get("page", 1), per_page=10)
            context["case_table"] = table

        return context
