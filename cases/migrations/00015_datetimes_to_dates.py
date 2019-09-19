from datetime import date

from tqdm import tqdm

from django.db import migrations, models
import django_import_data.mixins


def datetime_to_date(dt):
    return date(dt.year, dt.month, dt.day) if dt else dt


def copy_the_dates(apps, schema_editor):
    print("\nConverting Case DTs to dates...")
    # tqdm.write("")
    Case = apps.get_model("cases", "Case")
    db_alias = schema_editor.connection.alias
    for case in tqdm(Case.objects.using(db_alias).all()):
        case.sgrs_responded_on_date = datetime_to_date(case.sgrs_responded_on)
        case.completed_on_date = datetime_to_date(case.completed_on)
        case.date_recorded_date = datetime_to_date(case.date_recorded)
        case.save()

    print("Converting Facility DTs to dates...")
    Facility = apps.get_model("cases", "Facility")
    db_alias = schema_editor.connection.alias
    for facility in tqdm(Facility.objects.using(db_alias).all()):
        facility.sgrs_responded_on_date = datetime_to_date(facility.sgrs_responded_on)
        facility.save()


class Migration(migrations.Migration):

    dependencies = [("cases", "0014_finish_sgrs_service_num_to_char_field")]

    operations = [
        # Case
        migrations.AddField(
            model_name="case",
            name="sgrs_responded_on_date",
            field=models.DateField(
                null=True, blank=True, verbose_name="SGRS Responded On"
            ),
        ),
        migrations.AddField(
            model_name="case",
            name="completed_on_date",
            field=models.DateField(null=True, blank=True, verbose_name="Completed On"),
        ),
        migrations.AddField(
            model_name="case",
            name="date_recorded_date",
            field=models.DateField(null=True, blank=True, verbose_name="Date Recorded"),
        ),
        # Facility
        migrations.AddField(
            model_name="facility",
            name="sgrs_responded_on_date",
            field=models.DateField(
                null=True, blank=True, verbose_name="SGRS Responded On"
            ),
        ),
        migrations.RunPython(copy_the_dates),
        ## Remove fields original DT fields
        # Case
        migrations.RemoveField(model_name="case", name="sgrs_responded_on"),
        migrations.RemoveField(model_name="case", name="completed_on"),
        migrations.RemoveField(model_name="case", name="date_recorded"),
        # Facility
        migrations.RemoveField(model_name="facility", name="sgrs_responded_on"),
        ## Rename date fields in order to complete the replacement
        # Case
        migrations.RenameField(
            model_name="case",
            old_name="sgrs_responded_on_date",
            new_name="sgrs_responded_on",
        ),
        migrations.RenameField(
            model_name="case", old_name="completed_on_date", new_name="completed_on"
        ),
        migrations.RenameField(
            model_name="case", old_name="date_recorded_date", new_name="date_recorded"
        ),
        # Facility
        migrations.RenameField(
            model_name="facility",
            old_name="sgrs_responded_on_date",
            new_name="sgrs_responded_on",
        ),
    ]
