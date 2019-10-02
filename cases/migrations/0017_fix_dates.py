from datetime import datetime

from tqdm import tqdm

from django.db import migrations, models
import django_import_data.mixins


def fix_date_for_instance(instance, current_field_name, original_field_name):
    try:
        original_date_str = instance.model_import_attempt.model_importer.row_data.data[
            original_field_name
        ]
    except (AttributeError, KeyError) as error:
        original_date_str = None

    if original_date_str:
        original_date = datetime.strptime(original_date_str, "%m/%d/%Y %H:%M:%S").date()

        if getattr(instance, current_field_name) != original_date:
            tqdm.write(
                f"{instance} (last mod: {instance.modified_on}) date recorded was "
                f"{getattr(instance, current_field_name)}; now {original_date_str}"
            )
            setattr(instance, current_field_name, original_date)
    else:
        original_date = None

    return (instance, original_date, original_date_str)


def fix_date_recorded(case):
    return fix_date_for_instance(case, "date_recorded", "DATEREC")


def fix_sgrs_responded_on(case):
    return fix_date_for_instance(case, "sgrs_responded_on", "SGRSDATE")


def fix_completed_on(case):
    return fix_date_for_instance(case, "completed_on", "DATECOMP")


def fix_dates(apps, schema_editor):

    tqdm.write("\nFixing dates for all Cases...")
    Case = apps.get_model("cases", "Case")

    db_alias = schema_editor.connection.alias
    for case in tqdm(Case.objects.using(db_alias).all()):
        case, original_sgrs_responded_on, original_sgrs_responded_on_str = fix_sgrs_responded_on(
            case
        )
        case, original_completed_on, original_completed_on_str = fix_completed_on(case)
        case, original_date_recorded, original_date_recorded_str = fix_date_recorded(
            case
        )

        case.save()
        case.refresh_from_db()
        if original_date_recorded and case.date_recorded != original_date_recorded:
            raise AssertionError(
                f"Actual date_recorded: {case.date_recorded} | "
                f"original date_recorded: {original_date_recorded} | "
                f"original date_recorded string: {original_date_recorded_str}"
            )

        if original_completed_on and case.completed_on != original_completed_on:
            raise AssertionError(
                f"Actual completed_on: {case.completed_on} | "
                f"original completed_on: {original_completed_on} | "
                f"original completed_on string: {original_completed_on_str}"
            )

        if (
            original_sgrs_responded_on
            and case.sgrs_responded_on != original_sgrs_responded_on
        ):
            raise AssertionError(
                f"Actual sgrs_responded_on: {case.sgrs_responded_on} | "
                f"original sgrs_responded_on: {original_sgrs_responded_on} | "
                f"original sgrs_responded_on string: {original_sgrs_responded_on_str}"
            )

    tqdm.write("\nFixing dates for all Facilities...")
    Facility = apps.get_model("cases", "Facility")
    db_alias = schema_editor.connection.alias
    for facility in tqdm(Facility.objects.using(db_alias).all()):
        facility, original_sgrs_responded_on, original_sgrs_responded_on_str = fix_sgrs_responded_on(
            facility
        )

        facility.save()
        facility.refresh_from_db()
        if (
            original_sgrs_responded_on
            and facility.sgrs_responded_on != original_sgrs_responded_on
        ):
            raise AssertionError(
                f"Actual sgrs_responded_on: {facility.sgrs_responded_on} | "
                f"original sgrs_responded_on: {original_sgrs_responded_on} | "
                f"original sgrs_responded_on string: {original_sgrs_responded_on_str}"
            )


class Migration(migrations.Migration):
    dependencies = [("cases", "0016_datetimes_to_dates")]

    operations = [migrations.RunPython(fix_dates)]
