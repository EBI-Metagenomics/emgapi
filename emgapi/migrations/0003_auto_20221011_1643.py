# Generated by Django 3.2.12 on 2022-10-11 16:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('emgapi', '0002_auto_20221011_1541'),
    ]

    operations = [
        migrations.AddField(
            model_name='genomecatalogue',
            name='ftp_url',
            field=models.CharField(db_column='FTP_URL', default='http://ftp.ebi.ac.uk/pub/databases/metagenomics/mgnify_genomes/', max_length=200),
        ),
        migrations.AddField(
            model_name='genomecatalogue',
            name='pipeline_version_tag',
            field=models.CharField(db_column='PIPELINE_VERSION_TAG', default='v1.2.1', max_length=20),
        ),
    ]