# Generated by Django 2.2.3 on 2019-07-16 17:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("cases", "0009_auto_20190716_1336")]

    operations = [
        migrations.RenameField(
            model_name="attachment", old_name="path", new_name="file_path"
        ),
        migrations.AlterField(
            model_name="attachment",
            name="file_path",
            field=models.CharField(
                default=None,
                help_text="Path to the file that this is linked to",
                max_length=512,
                unique=True,
            ),
        ),
    ]
