# Generated by Django 2.1.5 on 2019-02-28 16:35

import cases.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0029_remove_facility_loc'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='comments',
            field=cases.models.SensibleTextField(blank=True),
        ),
        migrations.AlterField(
            model_name='case',
            name='comments',
            field=cases.models.SensibleTextField(blank=True),
        ),
        migrations.AlterField(
            model_name='facility',
            name='comments',
            field=cases.models.SensibleTextField(blank=True, default='', help_text='Additional information or comments from the applicant', verbose_name='Comments'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='facility',
            name='original_srs',
            field=models.ForeignKey(help_text='The spatial reference system of the original imported coordinates', on_delete=django.db.models.deletion.PROTECT, to='gis.PostGISSpatialRefSys', verbose_name='Original Spatial Reference System'),
        ),
        migrations.AlterField(
            model_name='facility',
            name='survey_1a',
            field=models.BooleanField(blank=True, null=True, verbose_name='Survey 1A'),
        ),
        migrations.AlterField(
            model_name='facility',
            name='survey_2c',
            field=models.BooleanField(blank=True, null=True, verbose_name='Survey 2C'),
        ),
        migrations.AlterField(
            model_name='facility',
            name='tpa',
            field=models.FloatField(blank=True, null=True, verbose_name='TPA'),
        ),
        migrations.AlterField(
            model_name='facility',
            name='usgs_dataset',
            field=cases.models.SensibleCharField(blank=True, choices=[('3m', '3m'), ('10m', '10m'), ('30m', '30m')], max_length=3, verbose_name='USGS Dataset'),
        ),
        migrations.AlterField(
            model_name='person',
            name='comments',
            field=cases.models.SensibleTextField(blank=True),
        ),
        migrations.AlterField(
            model_name='preliminarycase',
            name='comments',
            field=cases.models.SensibleTextField(blank=True),
        ),
        migrations.AlterField(
            model_name='preliminarycasegroup',
            name='comments',
            field=cases.models.SensibleTextField(blank=True),
        ),
        migrations.AlterField(
            model_name='preliminaryfacility',
            name='comments',
            field=cases.models.SensibleTextField(blank=True, default='', help_text='Additional information or comments from the applicant', verbose_name='Comments'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='preliminaryfacility',
            name='original_srs',
            field=models.ForeignKey(help_text='The spatial reference system of the original imported coordinates', on_delete=django.db.models.deletion.PROTECT, to='gis.PostGISSpatialRefSys', verbose_name='Original Spatial Reference System'),
        ),
        migrations.AlterField(
            model_name='preliminaryfacility',
            name='power_density_limit',
            field=models.FloatField(blank=True, null=True, verbose_name='Power Density Limit'),
        ),
        migrations.AlterField(
            model_name='preliminaryfacility',
            name='survey_1a',
            field=models.BooleanField(blank=True, null=True, verbose_name='Survey 1A'),
        ),
        migrations.AlterField(
            model_name='preliminaryfacility',
            name='survey_2c',
            field=models.BooleanField(blank=True, null=True, verbose_name='Survey 2C'),
        ),
        migrations.AlterField(
            model_name='preliminaryfacility',
            name='tpa',
            field=models.FloatField(blank=True, null=True, verbose_name='TPA'),
        ),
        migrations.AlterField(
            model_name='preliminaryfacility',
            name='usgs_dataset',
            field=cases.models.SensibleCharField(blank=True, choices=[('3m', '3m'), ('10m', '10m'), ('30m', '30m')], max_length=3, verbose_name='USGS Dataset'),
        ),
    ]