# Generated by Django 2.1.5 on 2019-02-28 14:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0027_auto_20190227_1626'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alsoknownas',
            name='data_source',
            field=models.CharField(choices=[('web', 'Web'), ('excel', 'Excel'), ('access_prelim_technical', 'Access Prelim. Technical Table'), ('access_technical', 'Access Technical Table'), ('access_prelim_application', 'Access Prelim. Application Table'), ('access_application', 'Access Application Table'), ('nam_application', 'NRQZ Analyzer Application'), ('fcc_asr', 'FCC ASR Database')], default='web', help_text='The source that this object was created from', max_length=25),
        ),
        migrations.AlterField(
            model_name='attachment',
            name='data_source',
            field=models.CharField(choices=[('web', 'Web'), ('excel', 'Excel'), ('access_prelim_technical', 'Access Prelim. Technical Table'), ('access_technical', 'Access Technical Table'), ('access_prelim_application', 'Access Prelim. Application Table'), ('access_application', 'Access Application Table'), ('nam_application', 'NRQZ Analyzer Application'), ('fcc_asr', 'FCC ASR Database')], default='web', help_text='The source that this object was created from', max_length=25),
        ),
        migrations.AlterField(
            model_name='case',
            name='data_source',
            field=models.CharField(choices=[('web', 'Web'), ('excel', 'Excel'), ('access_prelim_technical', 'Access Prelim. Technical Table'), ('access_technical', 'Access Technical Table'), ('access_prelim_application', 'Access Prelim. Application Table'), ('access_application', 'Access Application Table'), ('nam_application', 'NRQZ Analyzer Application'), ('fcc_asr', 'FCC ASR Database')], default='web', help_text='The source that this object was created from', max_length=25),
        ),
        migrations.AlterField(
            model_name='facility',
            name='data_source',
            field=models.CharField(choices=[('web', 'Web'), ('excel', 'Excel'), ('access_prelim_technical', 'Access Prelim. Technical Table'), ('access_technical', 'Access Technical Table'), ('access_prelim_application', 'Access Prelim. Application Table'), ('access_application', 'Access Application Table'), ('nam_application', 'NRQZ Analyzer Application'), ('fcc_asr', 'FCC ASR Database')], default='web', help_text='The source that this object was created from', max_length=25),
        ),
        migrations.AlterField(
            model_name='person',
            name='data_source',
            field=models.CharField(choices=[('web', 'Web'), ('excel', 'Excel'), ('access_prelim_technical', 'Access Prelim. Technical Table'), ('access_technical', 'Access Technical Table'), ('access_prelim_application', 'Access Prelim. Application Table'), ('access_application', 'Access Application Table'), ('nam_application', 'NRQZ Analyzer Application'), ('fcc_asr', 'FCC ASR Database')], default='web', help_text='The source that this object was created from', max_length=25),
        ),
        migrations.AlterField(
            model_name='preliminarycase',
            name='data_source',
            field=models.CharField(choices=[('web', 'Web'), ('excel', 'Excel'), ('access_prelim_technical', 'Access Prelim. Technical Table'), ('access_technical', 'Access Technical Table'), ('access_prelim_application', 'Access Prelim. Application Table'), ('access_application', 'Access Application Table'), ('nam_application', 'NRQZ Analyzer Application'), ('fcc_asr', 'FCC ASR Database')], default='web', help_text='The source that this object was created from', max_length=25),
        ),
        migrations.AlterField(
            model_name='preliminarycasegroup',
            name='data_source',
            field=models.CharField(choices=[('web', 'Web'), ('excel', 'Excel'), ('access_prelim_technical', 'Access Prelim. Technical Table'), ('access_technical', 'Access Technical Table'), ('access_prelim_application', 'Access Prelim. Application Table'), ('access_application', 'Access Application Table'), ('nam_application', 'NRQZ Analyzer Application'), ('fcc_asr', 'FCC ASR Database')], default='web', help_text='The source that this object was created from', max_length=25),
        ),
        migrations.AlterField(
            model_name='preliminaryfacility',
            name='data_source',
            field=models.CharField(choices=[('web', 'Web'), ('excel', 'Excel'), ('access_prelim_technical', 'Access Prelim. Technical Table'), ('access_technical', 'Access Technical Table'), ('access_prelim_application', 'Access Prelim. Application Table'), ('access_application', 'Access Application Table'), ('nam_application', 'NRQZ Analyzer Application'), ('fcc_asr', 'FCC ASR Database')], default='web', help_text='The source that this object was created from', max_length=25),
        ),
        migrations.AlterField(
            model_name='structure',
            name='data_source',
            field=models.CharField(choices=[('web', 'Web'), ('excel', 'Excel'), ('access_prelim_technical', 'Access Prelim. Technical Table'), ('access_technical', 'Access Technical Table'), ('access_prelim_application', 'Access Prelim. Application Table'), ('access_application', 'Access Application Table'), ('nam_application', 'NRQZ Analyzer Application'), ('fcc_asr', 'FCC ASR Database')], default='web', help_text='The source that this object was created from', max_length=25),
        ),
    ]