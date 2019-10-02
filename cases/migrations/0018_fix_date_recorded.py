from datetime import datetime

from tqdm import tqdm

from django.db import migrations, models
import django_import_data.mixins


def fix_date_recorded(apps, schema_editor):
    tqdm.write("Fixing date recorded")
    Case = apps.get_model("cases", "Case")
    db_alias = schema_editor.connection.alias
    for case in tqdm(Case.objects.using(db_alias).all()):
        try:
            original_date_recorded_str = case.model_import_attempt.model_importer.row_data.data[
                "DATEREC"
            ]
        except KeyError:
            original_date_recorded_str = None
        except AttributeError:
            pass

        if original_date_recorded_str:
            # tqdm.write(f"Case {case} date recoded was {case.date_recorded}; now {original_date_recorded_str}")
            original_date_recorded = datetime.strptime(
                original_date_recorded_str, "%m/%d/%Y %H:%M:%S"
            ).date()

            if case.date_recorded != original_date_recorded:
                case.date_recorded = original_date_recorded
                case.save()

            case.refresh_from_db()
            if case.date_recorded != original_date_recorded:
                raise AssertionError(
                    f"Actual daterec: {case.date_recorded} | original date rec str: {original_date_recorded} | parsed original date rec: {original_date_recorded_str}"
                )
        else:
            tqdm.write(
                f"Case {case.case_num} date recorded did not change: {case.date_recorded}"
            )


class Migration(migrations.Migration):

    dependencies = [("cases", "0017_dates_minus_one_day")]

    operations = [migrations.RunPython(fix_date_recorded)]
