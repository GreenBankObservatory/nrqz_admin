import os

from .base import *

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'nrqz_tchamber_dev',
        'USER': 'tchamber',
        'PASSWORD': '',
        'HOST': 'colossus.gb.nrao.edu',
        'PORT': '5432'
    }
}

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'nw20&ip%@lhstow7-u6!dx_+f@a#&93z3784$0_@_m-#@@dher'

ALLOWED_HOSTS = ["galileo", "galileo.gb.nrao.edu"]
