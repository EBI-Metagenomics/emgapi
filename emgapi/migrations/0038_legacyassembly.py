# Generated by Django 3.2.4 on 2022-01-18 20:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emgapi', '0037_remove_genome_num_genomes_non_redundant'),
    ]

    operations = [
        migrations.CreateModel(
            name='LegacyAssembly',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('legacy_accession', models.CharField(db_column='LEGACY_ACCESSION', db_index=True, max_length=80, verbose_name='Legacy assembly')),
                ('new_accession', models.CharField(db_column='NEW_ACCESSION', max_length=80, verbose_name='New accession')),
            ],
            options={
                'db_table': 'LEGACY_ASSEMBLY',
                'unique_together': {('legacy_accession', 'new_accession')},
            },
        ),
    ]
