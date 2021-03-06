# Generated by Django 2.2.3 on 2019-08-01 20:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0011_auto_20190716_1542'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='sgrs_service_num',
            field=models.PositiveIntegerField(blank=True, help_text='SGRS Service Num.', null=True, verbose_name='SGRS Service #'),
        ),
        migrations.AlterField(
            model_name='facility',
            name='original_srs',
            field=models.ForeignKey(blank=True, help_text='The spatial reference system of the original imported coordinates', null=True, on_delete=django.db.models.deletion.PROTECT, to='gis.PostGISSpatialRefSys', verbose_name='Original Spatial Reference System'),
        ),
        migrations.AlterField(
            model_name='lettertemplate',
            name='path',
            field=models.FilePathField(help_text="Save new files into '/home/tchamber/repos/nrqz_admin/letter_templates/' in order to select them here", max_length=512, path='/home/tchamber/repos/nrqz_admin/letter_templates/', unique=True),
        ),
        migrations.AlterField(
            model_name='preliminaryfacility',
            name='original_srs',
            field=models.ForeignKey(blank=True, help_text='The spatial reference system of the original imported coordinates', null=True, on_delete=django.db.models.deletion.PROTECT, to='gis.PostGISSpatialRefSys', verbose_name='Original Spatial Reference System'),
        ),
    ]
