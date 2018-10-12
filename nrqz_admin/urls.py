"""nrqz_admin URL Configuration"""

from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="/submissions")),
    path("applicants/", include("applicants.urls")),
    path("submissions/", include("submission.urls")),
    path("explorer/", include("explorer.urls")),
    path("admin/", admin.site.urls),
]
