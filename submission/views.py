from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from crispy_forms.layout import Submit, Layout, ButtonHolder, Div
from crispy_forms.helper import FormHelper

from .filters import FacilityFilter
from .tables import FacilityTable

from .models import Attachment, Submission, Facility

class SubmissionListView(ListView):
    model = Submission


class SubmissionDetailView(DetailView):
    model = Submission


def facility_list(request):
    filter_ = FacilityFilter(request.GET, queryset=Facility.objects.all())
    filter_.form.helper = FormHelper()
    filter_.form.helper.form_method = 'get'
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
