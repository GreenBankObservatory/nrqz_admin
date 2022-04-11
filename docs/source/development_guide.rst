Development Guide
=================

If you need to learn/change anything about the QZAT software itself, look here.


Design Philosophy
-----------------

Deliberately Simple UI
++++++++++++++++++++++

The UI for QZAT is pure, static Django HTML templates -- there is no (first-party) Javascript in the repo at all. This means that all pages are fully rendered server-side. There is obviously a performance cost here, but it is fast enough, and this keeps the UI development load very light.

There are a few exceptions to the static behavior:

- The Case Quick Jump uses `Django Autocomplete Light <https://django-autocomplete-light.readthedocs.io/en/master/>`_, which uses AJAX for the autocomplete functionality
- The Django Admin interface includes some Javascript widgets

Audits
++++++

All "import" actions should be transparent. If a file runs into errors, those errors should be obvious and available in their entirety via the web UI.

See :doc:`auditing_framework` for more details.

Tests
-----

No unit tests. Sorry.

This is a classic case of "prototype that made it into production". Development was very dynamic -- QZAT was used to build the requirements for itself. This meant that there were never any firm requirements for how it "should" work, and therefore there was a huge amount of overhead to writing tests

Repo Layout
-----------

Everything on the server side is done via Django. Like any large Django project, QZAT is split into apps:

- ``cases``: Models for the "core" QZAT functionality (``Case``, ``Facility``, etc.)
- ``audits``: Models for QZAT's "audit" functions
- ``docs``: This (Sphinx documentation source)
- ``importers``: Code for all Importers, data mappings, etc.
- ``misc``: Anything that doesn't fit elsewhere. Currently just holds custom Firefox ``user.js`` file
- ``letter_templates``: Stores the default Concurrence Letter Template file

Django Settings
---------------

QZAT uses an "env file" approach to managing secrets. This means that all secrets are stored in ``nrqz_admin/.env``. There is a single settings module: ``nrqz_admin/settings.py``. It is static, and committed to version control. Together, this means that all deployment options can (and should) be configured solely by modifying the ``.env`` file.

See the README for more information about getting started with this.

Data Import Process
-------------------

https://github.com/GreenBankObservatory/django-import-data/blob/master/example_project/django_import_data.ipynb
