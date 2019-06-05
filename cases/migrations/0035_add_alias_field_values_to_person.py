# Generated by Django 2.2.1 on 2019-06-05 19:32

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0034_auto_20190529_1106'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='alias_field_values',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, help_text='A list of dicts, each containing the differences between the primary model and an alias model', null=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='alias_field_values_summary',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, help_text='A summary of all unique differences between the alias models and the primary model', null=True),
        ),
    ]
