


class GenomeTypes(Enum):
    ISOLATE = 'isolate'
    MAG = 'mag'


class Genome(models.Model):
    accession = models.CharField(
        db_column='GENOME_ACCESSION', max_length=40, unique=True)
    last_update = models.DateTimeField(
        db_column='LAST_UPDATE', auto_now=True)
    first_created = models.DateTimeField(
        db_column='FIRST_CREATED', auto_now_add=True)

    completeness = models.FloatField(db_column='COMPLETENESS')
    contamination = models.FloatField(db_column='CONTAMINATION')
    rna_5s = models.FloatField(db_column='RNA_5S')
    rna_16s = models.FloatField(db_column='RNA_16S')
    rna_23s = models.FloatField(db_column='RNA_23S')
    trna = models.FloatField(db_column='T_RNA')
    num_genomes = models.IntegerField(db_column='NUM_GENOMES')
    num_proteins = models.IntegerField(db_column='NUM_PROTEINS')
    pangenome_size = models.IntegerField(db_column='PANGENOME_SIZE')
    core_prop = models.DecimalField(db_column='CORE_PROP', max_digits=6, decimal_places=3)
    accessory_prop = models.DecimalField(db_column='ACCESSORY_PROP', max_digits=6, decimal_places=3)
    eggnog_prop = models.DecimalField(db_column='EGGNOG_PROP', max_digits=6, decimal_places=3)
    ipr_prop = models.DecimalField(db_column='IPR_PROP', max_digits=6, decimal_places=3)
    length = models.IntegerField(db_column='LENGTH')
    n_contigs = models.IntegerField(db_column='N_CONTIGS')
    n_50 = models.IntegerField(db_column='N50')
    gc_content = models.DecimalField(db_column='GC_CONTENT', max_digits=6, decimal_places=3)
    type = models.CharField(db_column='TYPE', choices=[(tag, tag.value) for tag in GenomeTypes], max_length=80)


class CogCat(models.Model):
    name = models.CharField(db_column='NAME', max_length=80)


class CogCounts(models.Model):
    genome = models.ForeignKey(Genome, db_column='GENOME_ID', on_delete=models.CASCADE)
    cog = models.ForeignKey(CogCat, db_column='COG_ID', on_delete=models.DO_NOTHING)
    count = models.IntegerField(db_column='COUNT')


class KeggBrite(models.Model):
    kegg_brite_id = models.IntegerField(db_column='BRITE_ID')
    kegg_brite_name = models.CharField(db_column='NAME', max_length=80)
    kegg_brite_parent = models.ForeignKey("self", db_column='PARENT', null=True)


class KeggCounts(models.Model):
    genome = models.ForeignKey(Genome, db_column='GENOME_ID', on_delete=models.CASCADE)
    kegg = models.ForeignKey(KeggBrite, db_column='KEGG_ID', on_delete=models.DO_NOTHING)
    count = models.IntegerField(db_column='COUNT')

class IprEntry(models.Model):
    accession = models.CharField(db_column='ACCESSION', max_length=80)

class GenomeIprs(models.Model):
    genome = models.ForeignKey(Genome, db_column='GENOME_ID', on_delete=models.CASCADE)
    ipr_entry = models.ForeignKey(IprEntry, db_column='IPR_ID', on_delete=models.DO_NOTHING)
    rank = models.IntegerField(db_column='COUNT')