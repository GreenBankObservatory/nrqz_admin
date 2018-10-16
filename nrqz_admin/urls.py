"""nrqz_admin URL Configuration"""

from django.contrib import admin
from django.urls import include, path
from django.conf import settings

urlpatterns = [
    path("", include("submission.urls")),
    path("applicants/", include("applicants.urls")),
    path("explorer/", include("explorer.urls")),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
