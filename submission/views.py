from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.urls import reverse

from .models import Attachment, Submission, Facility

class SubmissionListView(ListView):
    model = Submission

class SubmissionDetailView(DetailView):
    model = Submission

class FacilityListView(ListView):
    model = Facility

class FacilityDetailView(DetailView):
    model = Facility

class AttachmentListView(ListView):
    model = Attachment

class AttachmentDetailView(DetailView):
    model = Attachment
