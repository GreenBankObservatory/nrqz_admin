# Generated by Django 2.2.16 on 2020-10-23 16:16

from django.db import migrations
import django_import_data.mixins


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0022_auto_20200303_1141'),
    ]

    operations = [
        migrations.AddField(
            model_name='facility',
            name='sgrs_work_order_num',
            field=django_import_data.mixins.SensibleCharField(blank=True, max_length=256, verbose_name='SGRS WO #'),
        ),
    ]