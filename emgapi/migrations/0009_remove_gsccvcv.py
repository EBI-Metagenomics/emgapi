# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-05-11 13:56
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emgapi', '0008_study_accession'),
    ]

    operations = [
        # migrations.AlterUniqueTogether(
        #     name='gsccvcv',
        #     unique_together=set([]),
        # ),
        migrations.RemoveField(
            model_name='gsccvcv',
            name='var_name',
        ),
        migrations.RemoveField(
            model_name='sampleann',
            name='var_val_cv',
        ),
        migrations.DeleteModel(
            name='GscCvCv',
        ),
    ]
