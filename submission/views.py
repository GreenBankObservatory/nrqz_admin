from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from django_filters.views import FilterView
import django_tables2 as tables

from .models import Attachment, Submission, Facility

class SubmissionListView(ListView):
    model = Submission

class SubmissionDetailView(DetailView):
    model = Submission


import django_filters

# from django.forms import Form
# class FacilityFilterForm(Form):


class FacilityFilter(django_filters.FilterSet):
    site_name = django_filters.CharFilter(lookup_expr='istartswith')
    call_sign = django_filters.CharFilter(lookup_expr='istartswith')
    latitude = django_filters.CharFilter(lookup_expr='startswith')
    longitude = django_filters.CharFilter(lookup_expr='startswith')
    freq_low = django_filters.RangeFilter(lookup_expr='range')
    freq_high = django_filters.RangeFilter(lookup_expr='range')
    amsl = django_filters.RangeFilter(lookup_expr='range')
    agl = django_filters.RangeFilter(lookup_expr='range')

    class Meta:
        model = Facility
        fields = ("site_name", "nrqz_id", "latitude", "longitude", "amsl", "agl", "freq_low", "freq_high")


from crispy_forms.helper import FormHelper

class FacilityFilterFormHelper(FormHelper):
    model = Facility
    # form_tag = False

    # def __init__(self, *args, **kwargs):
    #     super(FacilityFilterFormHelper, self).__init__(*args, **kwargs)
    #     print("FacilityFilterFormHelper")


# class PagedFilteredTableView(tables.SingleTableView):
#     filter_class = None
#     formhelper_class = None
#     context_filter_name = 'filter'

#     def get_queryset(self, **kwargs):
#         qs = super(PagedFilteredTableView, self).get_queryset()
#         self.filter = self.filter_class(self.request.GET, queryset=qs)
#         self.filter.form.helper = self.formhelper_class()
#         return self.filter.qs

#     def get_context_data(self, **kwargs):
#         context = super(PagedFilteredTableView, self).get_context_data()
#         context[self.context_filter_name] = self.filter
#         return context



class FacilityTable(tables.Table):
    site_name = tables.Column(linkify=True)
    class Meta:
        model = Facility
        fields = FacilityFilter.Meta.fields


class FacilityListView(tables.SingleTableMixin, FilterView):
    model = Facility
    table_class = FacilityTable
    filterset_class = FacilityFilter
    template_name = 'submission/facility_list.html'

# facility_list = FacilityListView.as_view()
from crispy_forms.layout import Submit, Layout, Fieldset, ButtonHolder, Div

def facility_list(request):
    filter_ = FacilityFilter(request.GET, queryset=Facility.objects.all())
    filter_.form.helper = FacilityFilterFormHelper()
    # filter_.form.helper.form_class = ''
    # filter_.form.helper.label_class = 'col-lg-3'
    filter_.form.helper.form_method = 'get'
    # filter_.form.helper.field_class = 'col-lg-9'
    filter_.form.helper.layout = Layout(
        Div(
            Div("site_name", "nrqz_id", css_class="col"),
            Div("latitude", "longitude", css_class="col"),
            Div("amsl", "agl", css_class="col"),
            Div("freq_low", "freq_high", css_class="col"),
            css_class="row"
        ),
        ButtonHolder(
            Submit('submit', 'Filter')
        )
    )
    
    # Can't get this to work with CBV, so I hacked this together
    # Use the filter's queryset, but with ONLY the fields specified in the filter
    # This is to prevent the table from coming up as blank initially
    table = FacilityTable(data=filter_.qs.only(*FacilityFilter.Meta.fields))
    table.paginate(page=request.GET.get('page', 1), per_page=25)
    return render(request, 'submission/facility_list.html', {'filter': filter_, 'table': table})

class FacilityDetailView(DetailView):
    model = Facility

class AttachmentListView(ListView):
    model = Attachment

class AttachmentDetailView(DetailView):
    model = Attachment
