"""Production Django settings"""

# pylint: disable=unused-wildcard-import,wildcard-import
from .base import *

ALLOWED_HOSTS = ["galileo", "galileo.gb.nrao.edu"]

INSTALLED_APPS += ["django_extensions"]

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "nrqz_admin_prod",
        "USER": "nrqz",
        "PASSWORD": "potato",
        "HOST": "galileo.gb.nrao.edu",
        "PORT": "5432",
    }
}

SECRET_KEY = "nw20&ip%@lhstow7-u6!dx_+f@a#&93z3784$0_@_m-#@@dher"

NRQZ_LETTER_TEMPLATE_DIR = "/home/nrqz.gb.nrao.edu/active/nrqz_admin/letter_templates"
STATIC_ROOT = "/home/nrqz.gb.nrao.edu/content"
