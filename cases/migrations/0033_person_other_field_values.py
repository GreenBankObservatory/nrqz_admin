# Generated by Django 2.2.1 on 2019-05-28 21:00

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0032_auto_20190528_1031'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='other_field_values',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]