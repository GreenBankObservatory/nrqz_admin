"""Base Django settings for nrqz_admin project."""

import os
from getpass import getuser
from pathlib import Path

import environ
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration


_user = getuser()
env = environ.Env(
    SENTRY_ENV=(str, f"{_user}_dev"),
    NRQZ_LETTER_TEMPLATE_DIR=(str, ""),
    STATIC_ROOT=(str, ""),
    ALLOWED_HOSTS=(list, []),
)
environ.Env.read_env()

BASE_DIR = Path(__file__).resolve().parent.parent

ALLOWED_HOSTS = env("ALLOWED_HOSTS")
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
NRQZ_LETTER_TEMPLATE_DIR = env("NRQZ_LETTER_TEMPLATE_DIR")
DATABASES = {
    # read os.environ['DATABASE_URL'] and raises ImproperlyConfigured exception if not found
    "default": env.db()
}
STATIC_ROOT = env("STATIC_ROOT")

# Application definition

# Make all requests atomic
ATOMIC_REQUESTS = True

INSTALLED_APPS = [
    "django_extensions",
    "dal",
    "dal_select2",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.postgres",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "django.contrib.sites",
    "stronghold",
    "django_tables2",
    "django_filters",
    "crispy_forms",
    "explorer",
    "watson",
    "django_import_data",
    "django_super_deduper",
    "tempus_dominus",
    "massadmin",
    "django_user_agents",
    "cases",
    "audits",
]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_user_agents.middleware.UserAgentMiddleware",
    "stronghold.middleware.LoginRequiredMiddleware",
]

ROOT_URLCONF = "nrqz_admin.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "registration/templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ],
            # TODO: Not a permanent solution!
            # "string_if_invalid": r"{{ %s }}",
        },
    }
]

WSGI_APPLICATION = "nrqz_admin.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/New_York"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = "/static/"

# Logging

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[%(asctime)s] %(levelname)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "verbose": {
            "format": (
                "[%(asctime)s] %(levelname)s"
                "[%(name)s.%(funcName)s:%(lineno)d] %(message)s"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "filters": {
        "require_debug_true": {"()": "django.utils.log.RequireDebugTrue"},
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            # "filters": ["require_debug_true"],
            "formatter": "simple",
        }
    },
    "loggers": {
        "cases": {"handlers": ["console"], "level": "DEBUG", "propagate": True},
        "tools": {"handlers": ["console"], "level": "DEBUG", "propagate": True},
        # "django_super_deduper": {"handlers": ["console"], "level": "DEBUG"},
    },
}


# django-explorer
# EXPLORER_CONNECTIONS = {"Default": "readonly"}
# EXPLORER_DEFAULT_CONNECTION = "readonly"
EXPLORER_CONNECTIONS = {"Default": "default"}
EXPLORER_DEFAULT_CONNECTION = "default"


# django-tables2
# Use Bootstrap4 table classes
DJANGO_TABLES2_TEMPLATE = "django_tables2/bootstrap4.html"


# django-crispy-forms
# Use Bootstrap4 form classes
CRISPY_TEMPLATE_PACK = "bootstrap4"


def FILTERS_VERBOSE_LOOKUPS():
    from django_filters.conf import DEFAULTS

    verbose_lookups = DEFAULTS["VERBOSE_LOOKUPS"].copy()
    verbose_lookups.update({"trigram_similar": "is similar to"})
    return verbose_lookups


SHELL_PLUS = "ipython"
SHELL_PLUS_PRE_IMPORTS = [
    (
        "django.contrib.gis.db.models.functions",
        ("Area", "Distance", "Value", "Length", "Perimeter"),
    ),
    ("tqdm", ("tqdm",)),
]
SHELL_PLUS_POST_IMPORTS = [("cases.models", ("Case",)), ("utils.constants", "*")]
STRONGHOLD_PUBLIC_NAMED_URLS = (
    "password_reset",
    "password_reset_done",
    "password_reset_confirm",
    "password_reset_complete",
)
STRONGHOLD_PUBLIC_URLS = ("^/accounts/reset/.*",)
SERVER_EMAIL = "noreply@nrao.edu"
DEFAULT_FROM_EMAIL = "noreply@nrao.edu"
EMAIL_HOST = "smtp.gb.nrao.edu"

ADMINS = (("Thomas Chamberlin", "tchamber@nrao.edu"),)

# We are bring in the latest tempus dominus assets ourselves, so we need to
# tell it not to do it itself
TEMPUS_DOMINUS_INCLUDE_ASSETS = False

# Match only docx files -- NOT the ~$tempfiles that Word creates
NRQZ_LETTER_TEMPLATE_REGEX = r"^[^~].*\.docx$"

# Remaps file paths based on the client host. This is necessary because unix and
# Windows hosts will access the filer using different paths. Since the server
# stores unix paths, for a Windows host to open them properly they will need to be
# remapped. But, we can't remap all of them, since all clients are not on Windows!
PATH_REMAPPINGS_BY_CLIENT_HOST = {
    "Windows": ("/home/code/nrqz/", "\\\\\\\\gbfiler/nrqz/")
}

# TODO: Enable memcached? Working, just need to see if it makes a difference
# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
#         "LOCATION": "127.0.0.1:11211",
#     }
# }
# USER_AGENTS_CACHE = "default"

sentry_sdk.init(
    environment=env("SENTRY_ENV"),
    integrations=[DjangoIntegration()],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True,
)

SITE_ID = 1
