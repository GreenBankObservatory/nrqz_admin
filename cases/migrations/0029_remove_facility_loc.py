# Generated by Django 2.1.5 on 2019-02-28 14:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0028_default_data_source_to_web'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='facility',
            name='loc',
        ),
    ]
