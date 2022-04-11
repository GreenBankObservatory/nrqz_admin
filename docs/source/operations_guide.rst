Operations Guide
================

If you need to learn/change anything about the way the QZAT software is run, look here.

Repositories
------------

QZAT consists of two repositories:

#. https://github.com/GreenBankObservatory/nrqz_admin
#. https://github.com/GreenBankObservatory/django-import-data

Both are managed by the GBO Organization. If you do not already have access to this organization, you will need to request it from SDD. See the README in each repository for details on how to set up a development environment.

Scheduled Tasks
---------------

Scheduled tasks for QZAT are all run by the cron daemon for ``nrqz@galileo``. These are well-documented in the crontab itself, but here they are in plain English for convenience:

- Every 2 minutes, refresh File Importers for all files modified in the last 10 minutes
- Each night, all File Importers are refreshed (re-hashed, existence-checked, etc.)
- Every hour, age of latest backup is checked
- Every hour, database is backed up
- New Letter Templates are generated (if new .docx files are found), via ``gen_letter_templates`` management command

Deployment
----------

There is currently only one deployment: ``/home/nrqz.gb.nrao.edu/``

Apache
++++++

This is a standard NRAO-style Apache deployment. The Virtual Host config file is located at ``/home/nrqz.gb.nrao.edu/conf/nrqz.conf``.

The Virtual Host is very simple:

1. All HTTP traffic is redirected to the HTTPS Virtual Host
2. All static content is served by Apache, from ``/home/nrqz.gb.nrao.edu/content/``
3. All other traffic is reverse-proxied to Gunicorn/Django

Django
++++++

Django is deployed to ``/home/nrqz.gb.nrao.edu/active/nrqz_admin``. Updates are made simply by pulling new code to the repo. A restart must then be performed via ``$ barnum nrqz@trent2 -- -- restart nrqz``

Changes to static files (e.g. if a new version of Bootstrap were being used) must be copied to the `content` area Apache expects (``/home/nrqz.gb.nrao.edu/content/``) via ``$ manage.py collectstatic``. No restart is required after this.

PostgreSQL
++++++++++

QZAT currently requires PostgreSQL 9.6, with the `postgis <https://postgis.net/install/>`_ extension. There are two non-standard things about this:

1. RHEL7 uses PostgreSQL 9.2; 9.6 had to be installed by GBO Computing
2. RHEL7 does not supply the ``postgis`` extension. It had to be manually compiled and installed


Web Stack
---------

.. mermaid::

    flowchart LR
        user((User))

        subgraph gb.nrao.edu
            subgraph gboweb
                apache[[Apache]]
            end

            subgraph trent2
                gunicorn[[Gunicorn]]
                django[[Django]]
                psql[(PostgreSQL)]
            end
        end

        user<-->|HTTP|apache
        apache<-->|"reverse proxy (HTTP)"|gunicorn
        gunicorn<-->|WSGI|django<-->|SQL|psql

Process Management
------------------

QZAT processes are managed by a mixture of Systemd and Circus. Broadly, the Systemd side is managed by GBO Computing; Circus is managed by GBO Software.

.. mermaid::

    graph TD

        subgraph gb.nrao.edu
            subgraph gboweb
                gboweb_systemd[["Systemd<br>(using httpd.service)"]]
                apache[[Apache]]
            end

            subgraph trent2
                trent2_systemd[["Systemd<br>(using circus_nrqz_trent2.service)"]]
                trent2_circus[["Circus<br>(using ~nrqz/circus/trent2/circus.ini"]]
                gunicorn[[Gunicorn]]
                django[[Django]]
                psql[(PostgreSQL)]
            end
        end

        gboweb_systemd-->apache

        trent2_systemd-->trent2_circus
        trent2_circus-->gunicorn
        trent2_circus-->django
        trent2_circus-->psql


Common Tasks
------------

Restart Apache
--------------

To "restart Apache", what we really want to do is "reload" the Apache daemon on ``gboweb``. We can do this via:

.. code-block:: bash

    user@gboweb $ /bin/sudo /bin/systemctl reload-or-restart httpd

Note that this well affect *all* Virtual Hosts on ``gboweb``. However, it shouldn't result in any downtime.

This is typically done after changing the Virtual Host config file

Note also that you will need to be given sudo access under your personal Linux account to run this command on ``gboweb`` (send a helpdesk ticket in if this is the case)


Restart QZAT
------------

To "restart QZAT", what we really want to do is restart the Gunicorn/Django WSGI server. It is easiest to do this via barnum:

.. code-block:: bash

    $ barnum nrqz@trent2 -- -- restart nrqz

This is typically done after changing QZAT code, or if there are wierd problems with the QZAT website.

Make a Change to the QZAT Circus Config
---------------------------------------

To change "QZAT's Circus", what we really want to change is ``nrqz@trent2``'s ``circus.ini``: ``~nrqz/circus/trent2/circus.init``

After modifying this file, you *should* be able to ``$ barnum nrqz@trent2 -- -- reloadconfig``. If this doesn't seem to work, you can simply restart Circus entirely via ``$ barnum nrqz@trent2 -- -- quit`` (this will kill the Circus process, causing Systemd to restart it)

Make a Change to the QZAT Code
------------------------------

First, get your changes to origin:

1. Make your change
2. Commit it
3. Push it to ``git@github.com:GreenBankObservatory/nrqz_admin``


Then, as ``nrqz``:

1. ``$ cdprod``
2. ``$ git pull origin release``
3. If you've changed any static files: ``$ manage.py collectstatic``
4. Restart QZAT: ``$ barnum nrqz@trent2 -- -- restart nrqz``



