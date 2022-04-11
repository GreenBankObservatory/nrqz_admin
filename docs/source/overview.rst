Overview
========

The NRQZ Administration Tool (QZAT) is a Django-based web application for managing administrative data for the National Radio Quiet Zone (NRQZ) Office located in Green Bank, WV.

QZAT is maintained by the GBO Software Development Division (SDD).

- For information on *using* QZAT, see the :doc:`user_guide`
- For information on *developing* QZAT, see the :doc:`development_guide`
- For information on *deploying* QZAT, see the :doc:`operations_guide`

Background
----------

QZAT development began in October, 2018, and ended in October, 2019. The sole developer and current maintainer is Thomas Chamberlin. The early goal was somewhat lofty: to automate a significant portion of the NRQZ coordination process. It became clear early on that this would be a lot more work than expected: there was no standardized format for submitting data for coordination, nor any easy way of importing the existing data into a single database. So, the initial phase of QZAT development was fairly narrow in scope:

1. Create a database capable of holding all "applicant data" (data about applicants and case files) and "technical data" (data about radio transmitters)
2. Import all existing digital NRQZ coordination records into this database
3. Create a web interface for accessing and manipulating this database (e.g. creating new case files and importing new technical data)


QZAT Web Interface
------------------

QZAT is hosted at https://nrqz.gb.nrao.edu. QZAT is basically a fancy administrative interface. This essentially means that the web UI closely resembles the database schema. There are "index" views for each table that allow searching, and "detail" views that show information about a single table.


QZAT is only accessible to logged-in users via the internal network. It uses the standard Django authentication system, which means that user accounts must be manually created before they can use the site -- there is no link between QZAT accounts and "computing" (Linux/Windows) accounts, etc. There is no public portion of the website -- everything is restricted to logged-in users.


