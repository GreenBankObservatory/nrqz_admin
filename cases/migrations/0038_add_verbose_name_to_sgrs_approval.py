# Generated by Django 2.2.1 on 2019-06-06 17:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0037_delete_alsoknownas'),
    ]

    operations = [
        migrations.AlterField(
            model_name='facility',
            name='sgrs_approval',
            field=models.BooleanField(blank=True, null=True, verbose_name='SGRS Approval'),
        ),
    ]
