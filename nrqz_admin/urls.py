"""nrqz_admin URL Configuration"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('submission/', include('submission.urls')),
    path('explorer/', include('explorer.urls')),
    path('admin/', admin.site.urls),
]
