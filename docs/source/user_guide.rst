User Guide
==========

For people who are *using* QZAT

QZAT Design
-----------

Here we will discuss the design and layout of the QZAT web application, and the data import processes

QZAT Core
+++++++++

QZAT consists primarily of the following entities:

1. Cases: Administrative information about a given case (e.g. comments about the case, "Freq. Coord. Num.", information about Sugar Grove)
2. People: Information about a given person (e.g. name, phone number)
3. Attachments: Simple paths to a given file or URL
4. Facilities: Technical information about a given radio transmitter (e.g. geographic location, elevation, bandwidth)


.. mermaid::

    flowchart LR
        case[Case]
        facility[Facility]
        attachment[Attachment]
        person[Person]
        case-->facility
        case-->|applicant|person
        case-->|contact|person
        case-->attachment
        facility-->attachment

QZAT is a web-based administrative dashboard. This essentially means that it is a web interface to a database, without a whole lot of extra stuff. This means that the layout of the website closely resembles the layout of the database itself.

For each entity above there are two primary web views:

1. The "index" view: a searchable/filterable list of **all** entities of a given type (e.g. the Case Index). This typically displays all of the rows of a given table
2. The "detail" view: a detailed view of a **single** entity (e.g. the Case Detail). This typically displays all of the values of a given row of a given table


QZAT Auditing
+++++++++++++

The other main part of the QZAT website is under the "Audits" menu. This is metadata about the various imports that can be performed in QZAT. For example, when you import a **new** Excel workbook file, the following entities will be created:

1. A ``File Importer Batch`` (of very little utility here; this was used to group the initial bulk imports)
2. A ``File Importer``: A representation of a single file on disk. This stores things like the path to the file, and its hash (a unique representation of the file contents, so we can detect changes to it)
3. A ``File Import Attempt``: A representation of a single **attempt** to import a file. Whether the import succeeds or not, this FIA will be created (if it doesn't succeed, there will be errors indicating why)
4. One ``Row Data`` for every data row of the spreadsheet: these represent the raw data in the row, and can be used to verify that the data was actually read from the spreadsheet as expected
5. Several ``Model Import Attempt`` instances for every row of the spreadsheet: these represent an *attempt* to create a given model/entity instance. e.g. if a row has data about a given Facility, then QZAT will *attempt* to create that Facility in the database. If this succeeds, the MIA will link to the created instance. If it fails, the MIA will link to nothing, but will store useful debugging information about *why* this did not work.

This auditing framework is in fact more complicated than the QZAT schema itself. You probably won't need to look at this very often. You can read more in depth information about how it works in the :doc:`auditing_framework` docs.

Access Controls
+++++++++++++++

QZAT is accessible only via the "internal" NRAO/GBO intranet. That is, you will need to either be on-site at a GBO or NRAO facility, or otherwise have access to the internal network (via VPN/VNC/proxy/etc.) in order to even see the login page.

Other than the login page, there is no public portion of QZAT. There are two tiers of access once logged in: admin and non-admin. If you have been granted admin privileges, you will be able to access the `Django Admin pages <https://nrqz.gb.nrao.edu/admin/>`_. This will allow you to e.g. add new user accounts, or deactivate old ones.

.. mermaid::

    flowchart LR
        subgraph Internet
            external_user((External<br>User))
        end

        subgraph "NRAO Intranet"
            internal_user((Internal<br>User))
            unauthenticated["Not Logged In (Unauthenticated)"]

            subgraph QZAT
                authenticated["Logged In (Authenticated)"]
                is_admin["QZAT Admin"]
                web_ui{{Full Access to QZAT Web UI}}

                do_admin{{"Perform Administrative Actions<br>(e.g. add/deactivate user accounts)"}}
            end
        end

        external_user-.->|VPN/Proxy/VNC|unauthenticated
        internal_user-->unauthenticated
        unauthenticated-->|log in|authenticated
        authenticated-->web_ui
        authenticated-->|user has is_staff flag|is_admin
        is_admin-->do_admin

Data Import Flow
++++++++++++++++

QZAT knows how to import data from three different sources:

1. "NRAO AutoPath Applicant Submission Template" Excel Files
2. nrqzApplicationMaker: A GUI created by Art Peters (AKP Consulting Engineers)
3. An Access database. This contained both "applicant" and "technical" data, manually entered by the NRQZ Administrator

.. mermaid::

    flowchart LR
        subgraph QZAT
            nam_importer[importers.nrqz_analyzer]
            excel_importer[importers.excel]
            access_app[importers.import_access_application]
            access_tech[importers.import_access_technical]
            qzat_db[(QZAT DB)]
            qzat_wsgi[QZAT<br>Web Server]
        end

        applicant((NRQZ<br>Applicant))
        nrqz_admin_in((NRQZ<br>Administrator))
        nrqz_admin_out((NRQZ<br>Administrator))

        applicant-.->|deprecated|nam_files
        applicant-->|emails|excel_files
        nrqz_admin_in-.->|deprecated|access_db

        nam_files[nrqzApplicationMaker] -->|read from /home/nrqz| nam_importer -->|imported| qzat_db
        excel_files[Excel Files] -->|read from /home/nrqz| excel_importer -->|imported| qzat_db
        access_db[Access DB] -->|read from /home/nrqz| access_app -->|imported| qzat_db
        access_db[Access DB] -->|read from /home/nrqz| access_tech -->|imported| qzat_db

        qzat_db<-->qzat_wsgi
        qzat_wsgi<-->nrqz_admin_out

Operations
----------

Backups
+++++++

The QZAT database is backed up every hour. In case of catastrophic data loss, it is trivial to roll back to an earlier backup -- the most you will lose is an hour of work **as long as you notify SDD promptly**. The longer you wait, the older the most recent "clean" backup will be.


Use Cases
---------

Here are some concrete examples of things that you might need to do in QZAT.

Search for a Given Case
+++++++++++++++++++++++

Let's say we want to search for all Cases in which the Applicant is named George. You would navigate to the Case Index, then enter George in "Applicant name contains", then click "Filter" (`or click here <https://nrqz.gb.nrao.edu/cases/?applicant=George>`_)

Search for a Given Facility
+++++++++++++++++++++++++++

Let's say we want to search for all Facilities within 1km of the GBT. You would navigate to the Facility Index, then enter "0-1000" (unit is meters) into the "Distance to GBT" filter (`or click here <https://nrqz.gb.nrao.edu/facilities/?distance_to_gbt=0-1000>`_)

Jump Directly to a Given Case #
+++++++++++++++++++++++++++++++

If you already know the Case # you are looking for, you can simply type/paste it into the "Quick-jump to Case #" input in the top right of the header

Create a New Case
+++++++++++++++++

Navigate to the "New Case" form by clicking on "New Case" in the header (`or click here <https://nrqz.gb.nrao.edu/cases/create>`_). Fill out the form, adding/creating any necessary Attachments, then click Submit

You will probably now want to import one or more Excel Workbooks to create Facilities and link them to the Case


Import Facilities from Excel
++++++++++++++++++++++++++++

Each different type of importer is pointed to a specific directory on "the filer". The easiest way to import Excel files is to figure out which location that is, and save them to the directory. Once there, they will appear in the `Unimported Files Dashboard <https://nrqz.gb.nrao.edu/audits/unimported-files-dashboard/>`_, and can be imported in bulk there.

Import Facilities from a Specific Excel File
++++++++++++++++++++++++++++++++++++++++++++

Navigate to ``Misc. -> Import File`` to reach the "Import File(s)" page (`or click here <https://nrqz.gb.nrao.edu/audits/file-importers/create/>`_). Then simply paste the path to a given Excel file (both Windows or Linux paths are accepted), then click "Import File".

Generate a Concurrence Letter
+++++++++++++++++++++++++++++

To generate a concurrence letter, navigate to the Concurrence Letter Generation page via ``Misc. -> Letters`` (`or click here <https://nrqz.gb.nrao.edu/letters/>`_). Then select the Case(s) and/or Facilities that you wish to include, as well as the template file to use. Then click "Download", and a .docx file will be generated for you.

Add/Remove/Change Concurrence Letter Templates
++++++++++++++++++++++++++++++++++++++++++++++

If you need to add a new Template, simply copy the .docx file to "NRQZ Admin Data/Letter Templates". QZAT should pick up the new template within the next minute and register it for use.

To change a given template, you simply need to change the .docx file itself. No other changes are needed.

There is also a manual interface for Concurrence Letter Templates available `here <https://nrqz.gb.nrao.edu/admin/cases/lettertemplate/>`_, but it shouldn't be necessary.
