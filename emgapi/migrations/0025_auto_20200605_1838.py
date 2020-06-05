# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-06-05 18:38
from __future__ import unicode_literals

from django.db import migrations


def create_download_description(apps, schema_editor):
    DownloadDescriptionLabel = apps.get_model("emgapi", "DownloadDescriptionLabel")
    downloads = (
        ("mOTUs taxonomic profile", "mOTUs taxonomic profile"),
    )
    _downloads = list()
    for d in downloads:
        _downloads.append(
            DownloadDescriptionLabel(
                description=d[0],
                description_label=d[1]
            )
        )
    DownloadDescriptionLabel.objects.bulk_create(_downloads)


def create_group_types(apps, schema_editor):
    DownloadGroupType = apps.get_model("emgapi", "DownloadGroupType")
    group_types = (
        "Taxonomic analysis mOTU",
    )
    _groups = list()
    for group_type in group_types:
        _groups.append(
            DownloadGroupType(group_type=group_type)
        )
    DownloadGroupType.objects.bulk_create(_groups)


class Migration(migrations.Migration):
    dependencies = [
        ('emgapi', '0024_auto_20200505_1737'),
    ]

    operations = [
        migrations.RunPython(create_download_description),
        migrations.RunPython(create_group_types),
    ]
