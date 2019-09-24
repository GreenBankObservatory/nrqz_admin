# Generated by Django 2.2.5 on 2019-09-24 13:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0014_finish_sgrs_service_num_to_char_field'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='facility',
            name='latitude',
        ),
        migrations.RemoveField(
            model_name='facility',
            name='longitude',
        ),
        migrations.RemoveField(
            model_name='preliminaryfacility',
            name='latitude',
        ),
        migrations.RemoveField(
            model_name='preliminaryfacility',
            name='longitude',
        ),
        migrations.AlterField(
            model_name='case',
            name='is_federal',
            field=models.BooleanField(help_text='Gov.', null=True, verbose_name='Gov.'),
        ),
        migrations.AlterField(
            model_name='lettertemplate',
            name='path',
            field=models.FilePathField(help_text="Save new files into '/home/sandboxes/tchamber/repos/nrqz_admin/letter_templates' in order to select them here", max_length=512, path='/home/sandboxes/tchamber/repos/nrqz_admin/letter_templates', unique=True),
        ),
        migrations.AlterField(
            model_name='preliminarycase',
            name='is_federal',
            field=models.BooleanField(help_text='Gov.', null=True, verbose_name='Gov.'),
        ),
    ]
