# Generated by Django 3.2.18 on 2023-11-08 09:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emgapi', '0011_analysisjob_analysis_summary_json'),
    ]

    operations = [
        migrations.AlterField(
            model_name='publication',
            name='pub_type',
            field=models.CharField(blank=True, db_column='PUB_TYPE', max_length=300, null=True),
        ),
    ]
