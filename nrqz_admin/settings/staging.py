from .base import *


ALLOWED_HOSTS = ["galileo", "galileo.gb.nrao.edu"]

DEBUG = True

DATABASES = {
    "readonly": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "nrqz_admin_beta",
        "USER": "nrqz_readonly",
        "PASSWORD": "",
        "HOST": "galileo.gb.nrao.edu",
        "PORT": "5432",
    },
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "nrqz_admin_beta",
        "USER": "nrqz",
        "PASSWORD": "",
        "HOST": "galileo.gb.nrao.edu",
        "PORT": "5432",
    },
}

SECRET_KEY = "nw20&ip%@lhstow7-u6!dx_+f@a#&93z3784$0_@_m-#@@dher"
