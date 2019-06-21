# Generated by Django 2.2.2 on 2019-06-21 20:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0005_fancycasegroup'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='preliminarycasegroup',
            name='model_import_attempt',
        ),
        migrations.AlterModelOptions(
            name='casegroup',
            options={},
        ),
        migrations.RemoveField(
            model_name='case',
            name='case_group',
        ),
        migrations.RemoveField(
            model_name='casegroup',
            name='data_source',
        ),
        migrations.RemoveField(
            model_name='casegroup',
            name='is_active',
        ),
        migrations.RemoveField(
            model_name='casegroup',
            name='model_import_attempt',
        ),
        migrations.RemoveField(
            model_name='preliminarycase',
            name='pcase_group',
        ),
        migrations.AddField(
            model_name='casegroup',
            name='cases',
            field=models.ManyToManyField(blank=True, related_name='case_groups', to='cases.Case'),
        ),
        migrations.AddField(
            model_name='casegroup',
            name='pcases',
            field=models.ManyToManyField(blank=True, related_name='case_groups', to='cases.PreliminaryCase'),
        ),
        migrations.DeleteModel(
            name='FancyCaseGroup',
        ),
        migrations.DeleteModel(
            name='PreliminaryCaseGroup',
        ),
    ]
