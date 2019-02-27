import getpass
from .base import *

user = getpass.getuser()

# Possibly important for import speed?
DEBUG = True
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INSTALLED_APPS += ["django_extensions", "django-resetdb", "debug_toolbar"]

DATABASES = {
    # "readonly": {
    #     "ENGINE": "django.db.backends.postgresql",
    #     "NAME": f"nrqz_{user}_dev",
    #     "USER": "postgres",
    #     "PASSWORD": "",
    #     "HOST": "galileo.gb.nrao.edu",
    #     "PORT": "5432",
    # },
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": f"nrqz_{user}_dev",
        "USER": "tchamber",
        "PASSWORD": "potato",
        "HOST": "galileo.gb.nrao.edu",
        "PORT": "5432",
        # Possibly important for import speed?
        "CONN_MAX_AGE": None,
    }
}

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "nw20&ip%@lhstow7-u6!dx_+f@a#&93z3784$0_@_m-#@@dher"

ALLOWED_HOSTS = ["galileo", "galileo.gb.nrao.edu"]

# django-debug-toolbar
INTERNAL_IPS = ["10.16.96.146", "10.16.96.90", "192.33.116.185"]

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

NRQZ_LETTER_TEMPLATE_DIR = "/home/sandboxes/tchamber/repos/nrqz_admin/letter_templates"
NRQZ_ATTACHMENT_DIR = "/home/sandboxes/tchamber/projects/nrqz_admin"
