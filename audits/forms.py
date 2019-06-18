import json
import os
from pathlib import Path

from django import forms

from django_import_data.models import FileImporter


SCRIPT_DIR = Path(__file__).resolve().parent
SPEC_FILE = os.path.join(
    SCRIPT_DIR.parent, "cases", "management", "commands", "importer_spec.json"
)


def prettify_importer_name(name):
    """Convert names from the format "import_foo_bar" to "Foo Bar"
    """
    # Basic sanity check to avoid weird things from happening
    if name.startswith("import_"):
        return " ".join([part[0].upper() + part[1:] for part in name.split("_")][1:])
    else:
        return name


def generate_importer_name_choices():
    with open(SPEC_FILE) as fp:
        command_info = json.load(fp)
        return ((name, prettify_importer_name(name)) for name in command_info.keys())


class FileImporterForm(forms.ModelForm):
    class Meta:
        model = FileImporter
        fields = ("file_path", "importer_name")

    # file_path = forms.CharField(
    #     label="Path of file to import", help_text="", unique=True
    # )

    importer_name = forms.ChoiceField(
        help_text="The Importer to use",
        choices=generate_importer_name_choices(),
        # TODO: Would be nice to consilidate this somewhere
        initial="import_excel_application",
    )
