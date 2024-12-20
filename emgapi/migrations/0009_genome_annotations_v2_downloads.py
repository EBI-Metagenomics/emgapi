# Generated by Django 3.2.12 on 2022-11-23 15:04

from django.db import migrations


def create_v2_genome_download_description(apps, schema_editor):
    DownloadDescriptionLabel = apps.get_model("emgapi", "DownloadDescriptionLabel")

    DownloadDescriptionLabel.objects.create(
        description="AMR annotations produced by AMRFinderPlus",
        description_label="Genome AMRFinderPlus Annotation"
    )
    DownloadDescriptionLabel.objects.create(
        description="Unfiltered CRISPRCasFinder results file, including calls that have evidence level 1 and are less likely to be genuine",
        description_label="Genome CRISPRCasFinder Annotation"
    )
    DownloadDescriptionLabel.objects.create(
        description="Additional data for CRISPRCasFinder records reported in the CRISPRCasFinder GFF",
        description_label="Genome CRISPRCasFinder Additional Records"
    )
    DownloadDescriptionLabel.objects.create(
        description="Annotated viral sequence and mobile elements",
        description_label="Genome Mobilome Annotation"
    )
    DownloadDescriptionLabel.objects.create(
        description="List of genes in the pan-genome with their annotation and MGYG accessions.",
        description_label="Gene Presence / Absence list"
    )


def remove_v2_genome_download_description(apps, schema_editor):
    DownloadDescriptionLabel = apps.get_model("emgapi", "DownloadDescriptionLabel")
    DownloadDescriptionLabel.objects.filter(description_label__in=[
        "Genome AMRFinderPlus Annotation",
        "Genome CRISPRCasFinder Annotation",
        "Genome CRISPRCasFinder Additional Records",
        "Genome Mobilome Annotation",
        "Gene Presence / Absence list",
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('emgapi', '0008_auto_20221128_1715'),
    ]

    operations = [
        migrations.RunPython(
            code=create_v2_genome_download_description,
            reverse_code=remove_v2_genome_download_description,
        ),
    ]
