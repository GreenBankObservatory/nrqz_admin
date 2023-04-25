# NRQZ Admin Tool (QZAT)


## Installation

```bash
# Clone the repo
git clone https://github.com/GreenBankObservatory/nrqz_admin.git
# Instructions below assume you are at the repo root
cd nrqz_admin
# Create virtual environment
python3.7 -m venv /path/to/venv
# Activate virtual environment
source /path/to/venv/bin/activate
# Install poetry and update build tools
pip install -U pip setuptools wheel poetry
# Install dependencies from lockfile
poetry install

# All Python dependencies are now installed. We now need to configure Django
# Ensure secrets file will be user-readable only
umask 077
# First, copy the env-file template
cp nrqz_admin/.env.template nrqz_admin/.env
# Can reset your umask now
# Now edit the file to set the DATABASE_URL
```

You'll now need to set up some extensions in your DB. As a Postgres admin, log into your test DB. Then:

```sql
# Create the necessary extensions
CREATE EXTENSION pg_trgm;
CREATE EXTENSION postgis;

# You might need to change the owner of one of the postgis tables
ALTER TABLE public.spatial_ref_sys OWNER TO your_username;
```

A few final tasks:

```bash
# Create or copy an importer_spec.json file, e.g.
cp /path/to/importer_spec.json cases/management/commands/importer_spec.json
# Initialize your DB
python manage.py migrate
# Initialize the DB with some data
python tools/build_dev_data.py
# Create a user account that you can log into
python manage.py createsuperuser
```

Finally, you should be able to run the dev server and log in:

```bash
./manage.py runserver
```
