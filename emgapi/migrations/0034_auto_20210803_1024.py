# Generated by Django 3.2.4 on 2021-08-03 10:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emgapi', '0033_auto_20210719_1608'),
    ]

    operations = [
        migrations.AddField(
            model_name='genome',
            name='is_sentinel',
            field=models.BooleanField(db_column='IS_SENTINEL', default=False, help_text='Sentinel genomes are used to block accession number ranges'),
        ),
        migrations.AddField(
            model_name='genomecatalogue',
            name='intended_genome_count',
            field=models.IntegerField(blank=True, db_column='INTENDED_GENOME_COUNT', help_text='How many genomes are expected to need an accession number when later added to the catalogue.', null=True),
        ),
        migrations.AddField(
            model_name='genomecatalogue',
            name='suggested_max_accession_number',
            field=models.IntegerField(blank=True, db_column='SUGGESTED_MAX_ACCESSION_NUMBER', help_text='The maximum accession number suggested for use by the catalogue’s genomes', null=True),
        ),
        migrations.AddField(
            model_name='genomecatalogue',
            name='suggested_min_accession_number',
            field=models.IntegerField(blank=True, db_column='SUGGESTED_MIN_ACCESSION_NUMBER', help_text='The minimum accession number suggested for use by the catalogue’s genomes', null=True),
        ),
        migrations.AlterField(
            model_name='genomecatalogue',
            name='result_directory',
            field=models.CharField(blank=True, db_column='RESULT_DIRECTORY', max_length=100, null=True),
        ),
    ]
