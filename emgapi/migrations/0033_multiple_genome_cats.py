# Generated by Django 3.2 on 2021-06-15 09:39
import django
from django.db import migrations, models

downloads = (
    ("Protein sequence FASTA file of the species representative", "Predicted CDS",),
    ("DNA sequence FASTA file of the genome assembly of the species representative", "Nucleic Acid Sequence",),
    ("DNA sequence FASTA file index of the genome assembly of the species representative", "Nucleic Acid Sequence index",),
    ("Protein sequence of the accessory genome", "Protein sequence (accessory)",),
    ("Protein sequence of the core genome", "Protein sequence (core)",),
    ("eggNOG annotations of the protein coding sequences", "EggNog annotation",),
    ("eggNOG annotations of the core and accessory genes", "EggNog annotation (core and accessory)",),
    ("InterProScan annotation of the protein coding sequences", "InterProScan annotation",),
    ("InterProScan annotations of the core and accessory genes", "InterProScan annotation (core and accessory)",),
    ("Presence/absence binary matrix of the pan-genome across all conspecific genomes", "Gene Presence / Absence matrix",),
    ("Protein sequence FASTA file of core genes (>=90% of the " +
     "genomes with >=90% amino acid identity)", "Core predicted CDS",),
    ("Protein sequence FASTA file of accessory genes", "Accessory predicted CDS",),
    ("Protein sequence FASTA file of core and accessory genes", "Core & Accessory predicted CDS",),
    ("Genome GFF file with various sequence annotations", "Genome Annotation"),
    ("Phylogenetic tree of release genomes", 'Phylogenetic tree of release genomes')
)


def change_release_to_catalogue_download_description(apps, schema_editor):
    DownloadDescriptionLabel = apps.get_model("emgapi",
                                              "DownloadDescriptionLabel")
    release_genomes_label = DownloadDescriptionLabel.objects.get(description='Phylogenetic tree of release genomes')
    release_genomes_label.description_label = 'Phylogenetic tree of catalogue genomes'
    release_genomes_label.description = 'Phylogenetic tree of catalogue genomes'
    release_genomes_label.save()


def unchange_release_to_catalogue_download_description(apps, schema_editor):
    DownloadDescriptionLabel = apps.get_model("emgapi",
                                              "DownloadDescriptionLabel")
    catalogue_genomes_label = DownloadDescriptionLabel.objects.get(description='Phylogenetic tree of catalogue genomes')
    catalogue_genomes_label.description_label = 'Phylogenetic tree of release genomes'
    catalogue_genomes_label.description = 'Phylogenetic tree of release genomes'
    catalogue_genomes_label.save()


def give_catalogues_an_id(apps, schema_editor):
    GenomeCatalogue = apps.get_model("emgapi", "GenomeCatalogue")
    for catalogue in GenomeCatalogue.objects.all():
        catalogue.catalogue_id = catalogue.version
        catalogue.name = catalogue.version


def make_first_release_for_genome_be_only_genome_catalogue(apps, schema_editor):
    Genome = apps.get_model("emgapi", "Genome")
    for genome in Genome.objects.all():
        genome.catalogue_id = genome.releases.first().id


class Migration(migrations.Migration):

    dependencies = [
        ('emgapi', '0032_auto_20210615_0939'),
    ]

    operations = [
        # Change Release to GenomeCatalogue, and make genome -> catalogue a many to one relationship
        migrations.RenameModel(
            'Release',
            'GenomeCatalogue'
        ),
        migrations.AddField(
            model_name="genomecatalogue",
            name="catalogue_id",
            field=models.SlugField(db_column='CATALOGUE_ID', max_length=100, null=True)
        ),
        migrations.AddField(
            model_name="genomecatalogue",
            name="name",
            field=models.CharField(db_column='NAME', max_length=100, unique=True, null=True)
        ),
        migrations.RunPython(
            give_catalogues_an_id,
            migrations.RunPython.noop
        ),
        migrations.AlterField(
            model_name="genomecatalogue",
            name="catalogue_id",
            field=models.SlugField(db_column='CATALOGUE_ID', max_length=100, null=False)
        ),
        migrations.AlterField(
            model_name="genomecatalogue",
            name="name",
            field=models.CharField(db_column='NAME', max_length=100, unique=True, null=False)
        ),
        migrations.AddField(
            model_name='genome',
            name='catalogue',
            field=models.ForeignKey(db_column='GENOME_CATALOGUE', on_delete=django.db.models.deletion.CASCADE,
                                    to='emgapi.GenomeCatalogue', null=True),
        ),
        migrations.RunPython(
            make_first_release_for_genome_be_only_genome_catalogue,
            reverse_code=migrations.RunPython.noop
        ),
        migrations.RemoveField(
            model_name="genome",
            name="releases"
        ),
        migrations.AlterField(
            model_name="genome",
            name="catalogue",
            field=models.ForeignKey(db_column='GENOME_CATALOGUE', on_delete=django.db.models.deletion.CASCADE,
                                    to='emgapi.GenomeCatalogue', null=False),
        ),

        migrations.RunPython(
            change_release_to_catalogue_download_description,
            reverse_code=unchange_release_to_catalogue_download_description),

        migrations.AlterField(
            model_name='genome',
            name='catalogue',
            field=models.ForeignKey(db_column='GENOME_CATALOGUE', on_delete=django.db.models.deletion.CASCADE,
                                    related_name='genomes', to='emgapi.genomecatalogue'),
        ),
        migrations.AlterField(
            model_name='genomecatalogue',
            name='catalogue_id',
            field=models.SlugField(db_column='CATALOGUE_ID', max_length=100, serialize=False),
        ),

        migrations.RenameModel(
            'ReleaseDownload',
            'GenomeCatalogueDownload'
        ),
        migrations.RenameField(
            model_name='GenomeCatalogueDownload',
            old_name='release',
            new_name='genome_catalogue'
        ),
        migrations.AlterUniqueTogether(
            name='releasegenomes',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='releasegenomes',
            name='genome',
        ),
        migrations.RemoveField(
            model_name='releasegenomes',
            name='release',
        ),

        # Add new metadata fields to catalogue
        migrations.AddField(
            model_name='genomecatalogue',
            name='biome',
            field=models.ForeignKey(blank=True, db_column='BIOME_ID', null=True,
                                    on_delete=django.db.models.deletion.CASCADE, to='emgapi.biome'),
        ),
        migrations.AddField(
            model_name='genomecatalogue',
            name='description',
            field=models.TextField(blank=True, db_column='DESCRIPTION',
                                   help_text='Use <a href="https://commonmark.org/help/" target="_newtab">markdown</a> for links and rich text.',
                                   null=True),
        ),
        migrations.AddField(
            model_name='genomecatalogue',
            name='protein_catalogue_description',
            field=models.TextField(blank=True, db_column='PROTEIN_CATALOGUE_DESCRIPTION',
                                   help_text='Use <a href="https://commonmark.org/help/" target="_newtab">markdown</a> for links and rich text.',
                                   null=True),
        ),
        migrations.AddField(
            model_name='genomecatalogue',
            name='protein_catalogue_name',
            field=models.CharField(blank=True, db_column='PROTEIN_CATALOGUE_NAME', max_length=100, null=True),
        ),

        migrations.AlterField(
            model_name='genomecatalogue',
            name='result_directory',
            field=models.CharField(blank=True, db_column='RESULT_DIRECTORY', max_length=100, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='genomecatalogue',
            unique_together={('biome', 'version')},
        ),
        migrations.AlterModelTable(
            name='genomecatalogue',
            table='GENOME_CATALOGUE',
        ),

        migrations.RemoveField(
            model_name='genomecatalogue',
            name='first_created',
        ),
        migrations.RemoveField(
            model_name='genomecatalogue',
            name='genomes',
        ),
        migrations.DeleteModel(
            name='ReleaseGenomes',
        ),
        migrations.AlterUniqueTogether(
            name='genomecataloguedownload',
            unique_together={('realname', 'alias')},
        ),
        migrations.AlterField(
            model_name='genomecataloguedownload',
            name='genome_catalogue',
            field=models.ForeignKey(db_column='GENOME_CATALOGUE_ID', on_delete=django.db.models.deletion.CASCADE,
                                    to='emgapi.genomecatalogue'),
        ),
        migrations.AlterModelTable(
            name='genomecataloguedownload',
            table='GENOME_CATALOGUE_DOWNLOAD',
        ),
    ]
