# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2019-07-09 10:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import emgapi.models


group_types = (
    "Genome analysis",
    "Pan-Genome analysis",
    "Genome release set"
)


def add_group_types(apps, schema_editor):
    DownloadGroupType = apps.get_model("emgapi", "DownloadGroupType")
    _groups = list()
    for group_type in group_types:
        _groups.append(
            DownloadGroupType(group_type=group_type)
        )
    DownloadGroupType.objects.bulk_create(_groups)


def remove_group_types(apps, schema_editor):
    DownloadGroupType = apps.get_model("emgapi", "DownloadGroupType")
    DownloadGroupType.objects.filter(group_type__in=group_types).delete()


file_formats = (
    ("TAB", "tab", False),
    ("GFF", "gff", False),
    ("JSON", "json", False),
)


def add_fileformats(apps, schema_editor):
    FileFormat = apps.get_model("emgapi", "FileFormat")
    _formats = list()
    for file_format in file_formats:
        _formats.append(
            FileFormat(
                format_name=file_format[0],
                format_extension=file_format[1],
                compression=file_format[2],
            )
        )
    FileFormat.objects.bulk_create(_formats)


def remove_file_formats(apps, schema_editor):
    FileFormat = apps.get_model("emgapi", "FileFormat")
    for name, ext, compression in file_formats:
        FileFormat.objects.filter(format_name=name,
                                 format_extension=ext,
                                 compression=compression).delete()


downloads = (
    ("Protein coding sequences of the reference genome.", "Genome CDS",),
    ("Genome sequence of the reference genome.", "Genome Assembly",),
    ("Protein sequence of the accessory genome.", "Protein sequence (accessory)",),
    ("Protein sequence of the core genome", "Protein sequence (core)",),
    ("Raw output of eggNOG-mapper.", "EggNOG annotation results",),
    ("Raw output of eggNOG-mapper.", "EggNOG annotation results",),
    ("Raw output of InterProScan", "InterProScan annotation results",),
    ("Raw output of InterProScan", "InterProScan annotation results",),
    ("Matrix of gene presence/absence of the pan-genome across all genomes", "Gene Presence / Absence matrix",),
    ("Protein sequence FASTA file of the core genes (>90% of the genomes)", "Core genes",),
    ("Protein sequence FASTA file of the accessory genes", "Accessory genes",),
    ("Protein sequence FASTA of both core and accessory genes", "Core & Accessory genes",),
    ('Genome GFF', 'Genome GFF'),
    ('Phylogenetic tree', 'Phylogenetic tree')
)


def add_download_description(apps, schema_editor):
    DownloadDescriptionLabel = apps.get_model("emgapi",
                                              "DownloadDescriptionLabel")
    _downloads = list()
    for d in downloads:
        _downloads.append(
            DownloadDescriptionLabel(
                description=d[0],
                description_label=d[1]
            )
        )
    DownloadDescriptionLabel.objects.bulk_create(_downloads)


def remove_download_description(apps, schema_editor):
    DownloadDescriptionLabel = apps.get_model("emgapi",
                                              "DownloadDescriptionLabel")
    for desc, desc_label in downloads:
        DownloadDescriptionLabel.objects.filter(description=desc,
                                                description_label=desc_label) \
            .delete()


class Migration(migrations.Migration):

    dependencies = [
        ('emgapi', '0012_auto_20190507_1219'),
    ]

    operations = [
        migrations.CreateModel(
            name='CogCat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_column='NAME', max_length=80, unique=True)),
                ('description', models.CharField(db_column='DESCRIPTION', max_length=80)),
            ],
            options={
                'db_table': 'COG',
            },
        ),
        migrations.CreateModel(
            name='Genome',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accession', models.CharField(db_column='GENOME_ACCESSION', max_length=40, unique=True)),
                ('ena_genome_accession', models.CharField(db_column='ENA_GENOME_ACCESSION', max_length=20, null=True, unique=True)),
                ('ena_sample_accession', models.CharField(db_column='ENA_SAMPLE_ACCESSION', max_length=20, null=True)),
                ('ena_study_accession', models.CharField(db_column='ENA_STUDY_ACCESSION', max_length=20, null=True)),
                ('ncbi_genome_accession', models.CharField(db_column='NCBI_GENOME_ACCESSION', max_length=20, null=True, unique=True)),
                ('ncbi_sample_accession', models.CharField(db_column='NCBI_SAMPLE_ACCESSION', max_length=20, null=True)),
                ('ncbi_study_accession', models.CharField(db_column='NCBI_STUDY_ACCESSION', max_length=20, null=True)),
                ('img_genome_accession', models.CharField(db_column='IMG_GENOME_ACCESSION', max_length=20, null=True, unique=True)),
                ('patric_genome_accession', models.CharField(db_column='PATRIC_GENOME_ACCESSION', max_length=20, null=True, unique=True)),
                ('length', models.IntegerField(db_column='LENGTH')),
                ('num_contigs', models.IntegerField(db_column='N_CONTIGS')),
                ('n_50', models.IntegerField(db_column='N50')),
                ('gc_content', models.FloatField(db_column='GC_CONTENT')),
                ('type', models.CharField(choices=[(emgapi.models.GenomeTypes('isolate'), 'isolate'), (emgapi.models.GenomeTypes('mag'), 'mag')], db_column='TYPE', max_length=80)),
                ('completeness', models.FloatField(db_column='COMPLETENESS')),
                ('contamination', models.FloatField(db_column='CONTAMINATION')),
                ('rna_5s', models.FloatField(db_column='RNA_5S')),
                ('rna_16s', models.FloatField(db_column='RNA_16S')),
                ('rna_23s', models.FloatField(db_column='RNA_23S')),
                ('trnas', models.FloatField(db_column='T_RNA')),
                ('nc_rnas', models.IntegerField(db_column='NC_RNA')),
                ('num_proteins', models.IntegerField(db_column='NUM_PROTEINS')),
                ('eggnog_coverage', models.FloatField(db_column='EGGNOG_COVERAGE')),
                ('ipr_coverage', models.FloatField(db_column='IPR_COVERAGE')),
                ('taxon_lineage', models.CharField(db_column='TAXON_LINEAGE', max_length=400)),
                ('num_genomes_total', models.IntegerField(db_column='PANGENOME_TOTAL_GENOMES', null=True)),
                ('num_genomes_non_redundant', models.IntegerField(db_column='PANGENOME_NON_RED_GENOMES', null=True)),
                ('pangenome_size', models.IntegerField(db_column='PANGENOME_SIZE', null=True)),
                ('pangenome_core_size', models.IntegerField(db_column='PANGENOME_CORE_PROP', null=True)),
                ('pangenome_accessory_size', models.IntegerField(db_column='PANGENOME_ACCESSORY_PROP', null=True)),
                ('pangenome_eggnog_coverage', models.FloatField(db_column='PANGENOME_EGGNOG_COV', null=True)),
                ('pangenome_ipr_coverage', models.FloatField(db_column='PANGENOME_IPR_COV', null=True)),
                ('last_update', models.DateTimeField(auto_now=True, db_column='LAST_UPDATE')),
                ('first_created', models.DateTimeField(auto_now_add=True, db_column='FIRST_CREATED')),
                ('result_directory', models.CharField(blank=True, db_column='RESULT_DIRECTORY', max_length=100, null=True)),
                ('biome', models.ForeignKey(db_column='BIOME_ID', on_delete=django.db.models.deletion.CASCADE, to='emgapi.Biome')),
            ],
            options={
                'db_table': 'GENOME',
            },
        ),
        migrations.CreateModel(
            name='GenomeCogCounts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('genome_count', models.IntegerField(db_column='GENOME_COUNT')),
                ('pangenome_count', models.IntegerField(db_column='PANGENOME_COUNT')),
                ('cog', models.ForeignKey(db_column='COG_ID', on_delete=django.db.models.deletion.DO_NOTHING, to='emgapi.CogCat')),
                ('genome', models.ForeignKey(db_column='GENOME_ID', on_delete=django.db.models.deletion.CASCADE, to='emgapi.Genome')),
            ],
            options={
                'db_table': 'GENOME_COG_COUNTS',
            },
        ),
        migrations.CreateModel(
            name='GenomeDownload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('realname', models.CharField(db_column='REAL_NAME', max_length=255)),
                ('alias', models.CharField(db_column='ALIAS', max_length=255)),
                ('description', models.ForeignKey(blank=True, db_column='DESCRIPTION_ID', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.DownloadDescriptionLabel')),
                ('file_format', models.ForeignKey(blank=True, db_column='FORMAT_ID', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.FileFormat')),
                ('genome', models.ForeignKey(db_column='GENOME_ID', on_delete=django.db.models.deletion.CASCADE, to='emgapi.Genome')),
                ('group_type', models.ForeignKey(blank=True, db_column='GROUP_ID', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.DownloadGroupType')),
                ('parent_id', models.ForeignKey(blank=True, db_column='PARENT_DOWNLOAD_ID', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='parent', to='emgapi.GenomeDownload')),
                ('subdir', models.ForeignKey(blank=True, db_column='SUBDIR_ID', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.DownloadSubdir')),
            ],
            options={
                'db_table': 'GENOME_DOWNLOAD',
                'ordering': ('group_type', 'alias'),
            },
        ),
        migrations.CreateModel(
            name='GenomeGeographicLocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'db_table': 'GENOME_GEOGRAPHIC_RANGE',
            },
        ),
        migrations.CreateModel(
            name='GenomeKeggClassCounts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('genome_count', models.IntegerField(db_column='GENOME_COUNT')),
                ('pangenome_count', models.IntegerField(db_column='PANGENOME_COUNT')),
                ('genome', models.ForeignKey(db_column='GENOME_ID', on_delete=django.db.models.deletion.CASCADE, to='emgapi.Genome')),
            ],
            options={
                'db_table': 'GENOME_KEGG_CLASS_COUNTS',
            },
        ),
        migrations.CreateModel(
            name='GenomeKeggModuleCounts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('genome_count', models.IntegerField(db_column='GENOME_COUNT')),
                ('pangenome_count', models.IntegerField(db_column='PANGENOME_COUNT')),
                ('genome', models.ForeignKey(db_column='GENOME_ID', on_delete=django.db.models.deletion.CASCADE, to='emgapi.Genome')),
            ],
            options={
                'db_table': 'GENOME_KEGG_MODULE_COUNTS',
            },
        ),
        migrations.CreateModel(
            name='GenomeSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_column='NAME', max_length=40, unique=True)),
            ],
            options={
                'db_table': 'GENOME_SET',
            },
        ),
        migrations.CreateModel(
            name='GeographicLocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_column='CONTINENT', max_length=80, unique=True)),
            ],
            options={
                'db_table': 'GEOGRAPHIC_RANGE',
            },
        ),
        migrations.CreateModel(
            name='KeggClass',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('class_id', models.CharField(db_column='CLASS_ID', max_length=10, unique=True)),
                ('name', models.CharField(db_column='NAME', max_length=80)),
                ('parent', models.ForeignKey(db_column='PARENT', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.KeggClass')),
            ],
            options={
                'db_table': 'KEGG_CLASS',
            },
        ),
        migrations.CreateModel(
            name='KeggModule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_column='MODULE_NAME', max_length=10, unique=True)),
                ('description', models.CharField(db_column='DESCRIPTION', max_length=200)),
            ],
            options={
                'db_table': 'KEGG_MODULE',
            },
        ),
        migrations.CreateModel(
            name='Release',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.CharField(db_column='VERSION', max_length=20)),
                ('last_update', models.DateTimeField(auto_now=True, db_column='LAST_UPDATE')),
                ('first_created', models.DateTimeField(auto_now_add=True, db_column='FIRST_CREATED')),
                ('result_directory', models.CharField(db_column='RESULT_DIRECTORY', max_length=100)),
            ],
            options={
                'db_table': 'RELEASE',
            },
        ),
        migrations.CreateModel(
            name='ReleaseDownload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('realname', models.CharField(db_column='REAL_NAME', max_length=255)),
                ('alias', models.CharField(db_column='ALIAS', max_length=255)),
                ('description', models.ForeignKey(blank=True, db_column='DESCRIPTION_ID', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.DownloadDescriptionLabel')),
                ('file_format', models.ForeignKey(blank=True, db_column='FORMAT_ID', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.FileFormat')),
                ('group_type', models.ForeignKey(blank=True, db_column='GROUP_ID', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.DownloadGroupType')),
                ('parent_id', models.ForeignKey(blank=True, db_column='PARENT_DOWNLOAD_ID', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='parent', to='emgapi.ReleaseDownload')),
                ('release', models.ForeignKey(db_column='RELEASE_ID', on_delete=django.db.models.deletion.CASCADE, to='emgapi.Release')),
                ('subdir', models.ForeignKey(blank=True, db_column='SUBDIR_ID', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.DownloadSubdir')),
            ],
            options={
                'db_table': 'RELEASE_DOWNLOAD',
                'ordering': ('group_type', 'alias'),
            },
        ),
        migrations.CreateModel(
            name='ReleaseGenomes',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('genome', models.ForeignKey(db_column='GENOME_ID', on_delete=django.db.models.deletion.CASCADE, to='emgapi.Genome')),
                ('release', models.ForeignKey(db_column='RELEASE_ID', on_delete=django.db.models.deletion.CASCADE, to='emgapi.Release')),
            ],
            options={
                'db_table': 'RELEASE_GENOMES',
            },
        ),
        migrations.AddField(
            model_name='release',
            name='genomes',
            field=models.ManyToManyField(through='emgapi.ReleaseGenomes', to='emgapi.Genome'),
        ),
        migrations.AddField(
            model_name='genomekeggmodulecounts',
            name='kegg_module',
            field=models.ForeignKey(db_column='KEGG_MODULE', on_delete=django.db.models.deletion.DO_NOTHING, to='emgapi.KeggModule'),
        ),
        migrations.AddField(
            model_name='genomekeggclasscounts',
            name='kegg_class',
            field=models.ForeignKey(db_column='KEGG_ID', on_delete=django.db.models.deletion.DO_NOTHING, to='emgapi.KeggClass'),
        ),
        migrations.AddField(
            model_name='genomegeographiclocation',
            name='GeographicLocation',
            field=models.ForeignKey(db_column='COG_ID', on_delete=django.db.models.deletion.DO_NOTHING, to='emgapi.GeographicLocation'),
        ),
        migrations.AddField(
            model_name='genomegeographiclocation',
            name='genome',
            field=models.ForeignKey(db_column='GENOME_ID', on_delete=django.db.models.deletion.CASCADE, to='emgapi.Genome'),
        ),
        migrations.AddField(
            model_name='genome',
            name='cog_matches',
            field=models.ManyToManyField(through='emgapi.GenomeCogCounts', to='emgapi.CogCat'),
        ),
        migrations.AddField(
            model_name='genome',
            name='genome_set',
            field=models.ForeignKey(db_column='GENOME_SET_ID', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.GenomeSet'),
        ),
        migrations.AddField(
            model_name='genome',
            name='geo_origin',
            field=models.ForeignKey(db_column='GEOGRAPHIC_ORIGIN', on_delete=django.db.models.deletion.CASCADE, to='emgapi.GeographicLocation'),
        ),
        migrations.AddField(
            model_name='genome',
            name='kegg_classes',
            field=models.ManyToManyField(through='emgapi.GenomeKeggClassCounts', to='emgapi.KeggClass'),
        ),
        migrations.AddField(
            model_name='genome',
            name='kegg_modules',
            field=models.ManyToManyField(through='emgapi.GenomeKeggModuleCounts', to='emgapi.KeggModule'),
        ),
        migrations.AddField(
            model_name='genome',
            name='pangenome_geographic_range',
            field=models.ManyToManyField(related_name='geographic_range', to='emgapi.GeographicLocation'),
        ),
        migrations.AddField(
            model_name='genome',
            name='releases',
            field=models.ManyToManyField(through='emgapi.ReleaseGenomes', to='emgapi.Release'),
        ),
        migrations.AlterUniqueTogether(
            name='releasegenomes',
            unique_together=set([('genome', 'release')]),
        ),
        migrations.AlterUniqueTogether(
            name='releasedownload',
            unique_together=set([('realname', 'alias')]),
        ),
        migrations.AlterUniqueTogether(
            name='genomekeggmodulecounts',
            unique_together=set([('genome', 'kegg_module')]),
        ),
        migrations.AlterUniqueTogether(
            name='genomekeggclasscounts',
            unique_together=set([('genome', 'kegg_class')]),
        ),
        migrations.AlterUniqueTogether(
            name='genomedownload',
            unique_together=set([('realname', 'alias')]),
        ),
        migrations.AlterUniqueTogether(
            name='genomecogcounts',
            unique_together=set([('genome', 'cog')]),
        ),
        migrations.RunPython(add_group_types, reverse_code=remove_group_types),
        migrations.RunPython(add_fileformats,
                             reverse_code=remove_file_formats),
        migrations.RunPython(add_download_description,
                             reverse_code=remove_download_description),
    ]
