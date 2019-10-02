from datetime import timedelta

from tqdm import tqdm

from django.db import migrations, models
import django_import_data.mixins


def minus_one_day(apps, schema_editor):
    print("\nMoving Case dates back one day...")
    # tqdm.write("")
    Case = apps.get_model("cases", "Case")
    db_alias = schema_editor.connection.alias
    for case in tqdm(Case.objects.using(db_alias).all()):
        if case.sgrs_responded_on:
            case.sgrs_responded_on -= timedelta(days=1)
        if case.completed_on:
            case.completed_on -= timedelta(days=1)
        if case.date_recorded:
            case.date_recorded -= timedelta(days=1)
        case.save()

    print("\nMoving Facility dates back one day...")
    Facility = apps.get_model("cases", "Facility")
    db_alias = schema_editor.connection.alias
    for facility in tqdm(Facility.objects.using(db_alias).all()):
        if facility.sgrs_responded_on:
            facility.sgrs_responded_on -= timedelta(days=1)
            facility.save()


class Migration(migrations.Migration):

    dependencies = [("cases", "0016_datetimes_to_dates")]

    operations = [migrations.RunPython(minus_one_day)]
