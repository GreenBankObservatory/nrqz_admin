# Generated by Django 2.1.5 on 2019-02-26 15:37

import cases.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0024_auto_20190221_1259'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='agency_num',
            field=models.CharField(blank=True, help_text='Agency Num.', max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='case',
            name='case_num',
            field=models.PositiveIntegerField(db_index=True, default=cases.models.get_case_num, unique=True, verbose_name='Case Num.'),
        ),
        migrations.AlterField(
            model_name='case',
            name='sgrs_service_num',
            field=models.PositiveIntegerField(blank=True, help_text='SGRS Service Num.', null=True),
        ),
        migrations.AlterField(
            model_name='preliminarycase',
            name='case_num',
            field=models.PositiveIntegerField(db_index=True, default=cases.models.get_pcase_num, unique=True, verbose_name='Prelim. Case Num.'),
        ),
    ]