# Generated by Django 2.2.5 on 2019-10-07 17:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0016_datetimes_to_dates'),
    ]

    operations = [
        migrations.AlterField(
            model_name='preliminarycase',
            name='completed_on',
            field=models.DateField(blank=True, null=True, verbose_name='Completed On'),
        ),
        migrations.AlterField(
            model_name='preliminarycase',
            name='date_recorded',
            field=models.DateField(blank=True, null=True, verbose_name='Date Recorded'),
        ),
    ]
