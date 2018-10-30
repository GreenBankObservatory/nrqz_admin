import getpass
from .base import *

user = getpass.getuser()

DEBUG = True
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INSTALLED_APPS += ["django_extensions", "django-resetdb", "debug_toolbar"]

DATABASES = {
    "readonly": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": f"nrqz_{user}_dev",
        "USER": "readonly",
        "PASSWORD": "",
        "HOST": "galileo.gb.nrao.edu",
        "PORT": "5432",
    },
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": f"nrqz_{user}_dev",
        "USER": user,
        "PASSWORD": "",
        "HOST": "galileo.gb.nrao.edu",
        "PORT": "5432",
    },
}

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "nw20&ip%@lhstow7-u6!dx_+f@a#&93z3784$0_@_m-#@@dher"

ALLOWED_HOSTS = ["galileo", "galileo.gb.nrao.edu"]

# django-debug-toolbar
INTERNAL_IPS = ["10.16.96.146"]

# Enable DB logging
# LOGGING["loggers"].update(
#     {
#         "django.db.backends": {
#             "level": "DEBUG",
#             "handlers": ["console"],
#             "propagate": False,
#         }
#     }
# )
