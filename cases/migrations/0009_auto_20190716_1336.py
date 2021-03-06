# Generated by Django 2.2.3 on 2019-07-16 17:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0008_casegroup_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachment',
            name='file_modified_on',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='attachment',
            name='hash_checked_on',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='attachment',
            name='hash_on_disk',
            field=models.CharField(blank=True, help_text='SHA-1 hash of the file on disk. If blank, the file is missing', max_length=40, null=True, unique=True),
        ),
    ]
