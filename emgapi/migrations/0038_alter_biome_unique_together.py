# Generated by Django 3.2.7 on 2022-02-24 16:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emgapi', '0037_remove_genome_num_genomes_non_redundant'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='biome',
            unique_together={('lineage', 'biome_name')},
        ),
    ]
