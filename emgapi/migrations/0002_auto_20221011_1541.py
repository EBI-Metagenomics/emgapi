# Generated by Django 3.2.12 on 2022-10-11 15:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('emgapi', '0001_squashed_0043_auto_20220811_1308'),
    ]

    operations = [
        migrations.AddField(
            model_name='genomecatalogue',
            name='unclustered_genome_count',
            field=models.IntegerField(blank=True, db_column='UNCLUSTERED_GENOME_COUNT', help_text='Total number of genomes in the catalogue (including cluster reps and members)', null=True),
        ),
        migrations.AlterField(
            model_name='genomecatalogue',
            name='genome_count',
            field=models.IntegerField(blank=True, db_column='GENOME_COUNT', help_text='Number of genomes available in the web database (species-level cluster reps only)', null=True),
        ),
    ]
