# Generated by Django 3.2.18 on 2023-09-12 17:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emgapi', '0011_analysisjob_job_operator_2'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='analysisjob',
            name='job_operator_2',
        ),
    ]
