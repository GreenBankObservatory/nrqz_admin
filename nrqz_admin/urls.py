"""nrqz_admin URL Configuration"""

from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.views.generic.base import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="/cases")),
    path("", include("cases.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("explorer/", include("explorer.urls")),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
