import logging
import os

from django.core.management import BaseCommand
from django.utils.text import slugify

from emgapi import models as emg_models

from ..lib.genome_util import sanity_check_genome_output, \
    sanity_check_catalogue_dir, find_genome_results, \
    get_genome_result_path, \
    read_tsv_w_headers, read_json, \
    apparent_accession_of_genome_dir

logger = logging.getLogger(__name__)

cog_cache = {}
ipr_cache = {}


class Command(BaseCommand):
    obj_list = list()
    results_directory = None
    genome_folders = None
    catalogue_obj = None
    catalogue_dir = None

    database = None

    def add_arguments(self, parser):
        parser.add_argument('results_directory', action='store', type=str, )
        parser.add_argument('catalogue_directory', action='store', type=str,
                            help='The folder within `results_directory` where the results files are. '
                                 'e.g. "genomes/skin/1.0/"')
        parser.add_argument('catalogue_name', action='store', type=str,
                            help='The name of this catalogue (without any version label), e.g. "Human Skin"')
        parser.add_argument('catalogue_version', action='store', type=str,
                            help='The version label. E.g. "1.0" or "2021-01"')
        parser.add_argument('gold_biome', action='store', type=str,
                            help="Primary biome for the catalogue, as a GOLD lineage. "
                                 "E.g. root:Host-Associated:Human:Digestive\\ System:Large\\ intestine")
        parser.add_argument('--database', type=str,
                            default='default')

    def handle(self, *args, **options):
        self.results_directory = os.path.realpath(options.get('results_directory').strip())
        if not os.path.exists(self.results_directory):
            raise FileNotFoundError('Results dir {} does not exist'
                                    .format(self.results_directory))

        catalogue_name = options['catalogue_name'].strip()
        version = options['catalogue_version'].strip()
        catalogue_dir = options['catalogue_directory'].strip()
        gold_biome = options['gold_biome'].strip()
        self.catalogue_dir = os.path.join(self.results_directory, catalogue_dir)

        self.database = options['database']
        self.catalogue_obj = self.get_catalogue(catalogue_name, version, gold_biome, catalogue_dir)

        logger.info("CLI %r" % options)

        genome_dirs = find_genome_results(self.catalogue_dir)
        logger.info(
            'Found {} genome dirs to upload'.format(len(genome_dirs)))

        [sanity_check_genome_output(d) for d in genome_dirs]

        sanity_check_catalogue_dir(self.catalogue_dir)

        for d in genome_dirs:
            self.upload_dir(d)

        self.upload_catalogue_files()
        self.catalogue_obj.calculate_genome_count()
        self.catalogue_obj.save()

    def get_catalogue(self, catalogue_name, catalogue_version, gold_biome, catalogue_dir):
        logging.warning('GOLD')
        logging.warning(gold_biome)
        biome = self.get_gold_biome(gold_biome)

        catalogue, _ = emg_models.GenomeCatalogue.objects \
            .using(self.database) \
            .get_or_create(
                catalogue_id=slugify('{0}-v{1}'.format(catalogue_name, catalogue_version).replace('.', '-')),
                defaults={
                    'version': catalogue_version,
                    'name': '{0} v{1}'.format(catalogue_name, catalogue_version),
                    'biome': biome,
                    'result_directory': catalogue_dir
                })
        return catalogue

    def upload_dir(self, directory):
        logger.info('Uploading dir: {}'.format(directory))
        genome, has_pangenome = self.create_genome(directory)
        self.upload_cog_results(genome, directory)
        self.upload_kegg_class_results(genome, directory)
        self.upload_kegg_module_results(genome, directory)
        self.upload_antismash_geneclusters(genome, directory)
        self.upload_genome_files(genome, directory, has_pangenome)

    def get_gold_biome(self, lineage):
        biome = emg_models.Biome.objects.using(self.database).filter(lineage__iexact=lineage).first()
        if not biome:
            raise emg_models.Biome.DoesNotExist()
        return biome

    def get_or_create_genome_set(self, setname):
        return emg_models.GenomeSet.objects.using(self.database).get_or_create(name=setname)[0]

    def prepare_genome_data(self, genome_dir):
        d = read_json(os.path.join(genome_dir, f'{apparent_accession_of_genome_dir(genome_dir)}.json'))

        has_pangenome = 'pangenome' in d
        d['biome'] = self.get_gold_biome(d['gold_biome'])
        d['genome_set'] = self.get_or_create_genome_set(d.get('genome_set', 'NCBI'))
        if has_pangenome:
            d.update(d['pangenome'])
            del d['pangenome']
        d.setdefault('num_genomes_total', 1)

        if 'num_genomes_non_redundant' in d:
            del d['num_genomes_non_redundant']

        if 'geographic_origin' in d:
            d['geo_origin'] = self.get_geo_location(d['geographic_origin'])
            del d['geographic_origin']

        del d['gold_biome']
        return d, has_pangenome

    def get_geo_location(self, location):
        return emg_models.GeographicLocation \
            .objects.using(self.database).get_or_create(name=location)[0]

    def attach_geo_location(self, genome, location):
        genome.pangenome_geographic_range.add(self.get_geo_location(location))

    def create_genome(self, genome_dir):
        data, has_pangenome = self.prepare_genome_data(genome_dir)

        geo_locations = data.get('geographic_range')
        data.pop('geographic_range', None)
        data.pop('genome_accession', None)

        data['result_directory'] = get_genome_result_path(genome_dir)
        data['catalogue'] = self.catalogue_obj
        g, created = emg_models.Genome.objects.using(self.database).update_or_create(
            accession=data['accession'],
            defaults=data)
        g.save(using=self.database)

        if geo_locations:
            [self.attach_geo_location(g, l) for l in geo_locations]

        return g, has_pangenome

    def upload_cog_results(self, genome, d):
        genome_cogs = os.path.join(d, 'genome', f'{genome.accession}_cog_summary.tsv')
        self.upload_cog_result(genome, genome_cogs)
        logger.info('Loaded Genome COG for {}'.format(genome.accession))

    def upload_cog_result(self, genome, f):
        counts = read_tsv_w_headers(f)
        for cc in counts:
            self.upload_cog_count(genome, cc)
        logger.info('Loaded Genome COG for {}'.format(genome.accession))

    def upload_cog_count(self, genome, cog_count):
        c_name = cog_count['COG_category']
        cog = self.get_cog_cat(c_name)

        count_val = int(cog_count['Counts'])

        defaults = {'genome_count': 0}

        count, created = emg_models.GenomeCogCounts.objects \
            .using(self.database) \
            .get_or_create(genome=genome,
                           cog=cog,
                           defaults=defaults)

        count.genome_count = count_val
        count.save(using=self.database)

    def get_cog_cat(self, c_name):
        return emg_models.CogCat.objects.using(self.database) \
            .get_or_create(name=c_name)[0]

    def upload_kegg_class_results(self, genome, d):
        genome_kegg_classes = os.path.join(d, 'genome', f'{genome.accession}_kegg_classes.tsv')
        self.upload_kegg_class_result(genome, genome_kegg_classes)
        logger.info(
            'Loaded Genome KEGG classes for {}'.format(genome.accession))

    def upload_kegg_class_result(self, genome, f):
        kegg_matches = read_tsv_w_headers(f)
        for kegg_match in kegg_matches:
            self.upload_kegg_class_count(genome, kegg_match)

    def get_kegg_class(self, kegg_cls_id):
        return emg_models.KeggClass.objects.using(self.database) \
            .get_or_create(class_id=kegg_cls_id)[0]

    def upload_kegg_class_count(self, genome, kegg_match):
        kegg_id = kegg_match['KEGG_class']
        kegg_class = self.get_kegg_class(kegg_id)

        count_val = int(kegg_match['Counts'])

        defaults = {'genome_count': 0}

        count, created = emg_models.GenomeKeggClassCounts.objects \
            .using(self.database) \
            .get_or_create(genome=genome,
                           kegg_class=kegg_class,
                           defaults=defaults)

        count.genome_count = count_val
        count.save(using=self.database)

    def upload_kegg_module_results(self, genome, d):
        genome_kegg_modules = os.path.join(d, 'genome', f'{genome.accession}_kegg_modules.tsv')
        self.upload_kegg_module_result(genome, genome_kegg_modules)
        logger.info(
            'Loaded Genome KEGG modules for {}'.format(genome.accession))

    def upload_kegg_module_result(self, genome, f):
        kegg_matches = read_tsv_w_headers(f)
        for kegg_match in kegg_matches:
            self.upload_kegg_module_count(genome, kegg_match)

    def get_kegg_module(self, name):
        return emg_models.KeggModule.objects.using(self.database) \
            .get_or_create(name=name)[0]

    def upload_kegg_module_count(self, genome, kegg_match):
        kegg_module_id = kegg_match['KEGG_module']
        kegg_module = self.get_kegg_module(kegg_module_id)

        count_val = int(kegg_match['Counts'])

        defaults = {'genome_count': 0}

        count, created = emg_models.GenomeKeggModuleCounts.objects \
            .using(self.database) \
            .get_or_create(genome=genome,
                           kegg_module=kegg_module,
                           defaults=defaults)

        count.genome_count = count_val
        count.save(using=self.database)

    def upload_antismash_geneclusters(self, genome, directory):
        """Upload AS results in the DB
        """
        file = os.path.join(directory, 'genome', 'geneclusters.txt')

        if not os.path.exists(file):
            logger.warning('Genome {} does not have antiSMASH geneclusters'.format(genome.accession))
            return

        with open(file, 'rt') as tsv:
            for row in tsv:
                *_, cluster, features, _ = row.split('\t')

                as_cluster, _ = emg_models.AntiSmashGC.objects \
                    .using(self.database) \
                    .get_or_create(name=cluster)

                count_val = len(features.split(';')) if len(features) else 0
                model, _ = emg_models.GenomeAntiSmashGCCounts.objects \
                    .using(self.database) \
                    .get_or_create(genome=genome, antismash_genecluster=as_cluster,
                                   genome_count=count_val)
                model.save(using=self.database)

            logger.info(
                'Loaded Genome AntiSMASH geneclusters for {}'.format(genome.accession))

    def upload_genome_files(self, genome, directory, has_pangenome):
        logger.info('Uploading genome files...')
        self.upload_genome_file(genome, directory, 'Predicted CDS (aa)', 'fasta',
                                genome.accession + '.faa', 'Genome analysis', 'genome', True)
        self.upload_genome_file(genome, directory, 'Nucleic Acid Sequence', 'fasta',
                                genome.accession + '.fna', 'Genome analysis', 'genome', True)
        self.upload_genome_file(genome, directory, 'Nucleic Acid Sequence index', 'fai',
                                genome.accession + '.fna.fai', 'Genome analysis', 'genome', True, )
        self.upload_genome_file(genome, directory, 'Genome Annotation', 'gff',
                                genome.accession + '.gff', 'Genome analysis', 'genome', True)
        self.upload_genome_file(genome, directory, 'Genome antiSMASH Annotation', 'gff',
                                genome.accession + '_antismash.gff', 'Genome analysis', 'genome', False)
        self.upload_genome_file(genome, directory, 'EggNog annotation', 'tsv',
                                genome.accession + '_eggNOG.tsv', 'Genome analysis', 'genome', False)
        self.upload_genome_file(genome, directory, 'InterProScan annotation', 'tsv',
                                genome.accession + '_InterProScan.tsv', 'Genome analysis', 'genome', False)
        self.upload_genome_file(genome, directory, 'Genome rRNA Sequence', 'fasta',
                                genome.accession + '_rRNAs.fasta', 'Genome analysis', 'genome', False)

        if has_pangenome:
            self.upload_genome_file(genome, directory, 'Pangenome core genes list', 'tab',
                                    'core_genes.txt', 'Pan-Genome analysis', 'pan-genome', False)
            self.upload_genome_file(genome, directory, 'Pangenome DNA sequence', 'fasta',
                                    'pan-genome.fna', 'Pan-Genome analysis', 'pan-genome', False)
            self.upload_genome_file(genome, directory,
                                    'Gene Presence / Absence matrix',
                                    'tsv', 'gene_presence_absence.Rtab', 'Pan-Genome analysis', 'pan-genome', False)
            self.upload_genome_file(genome, directory,
                                    'Pairwise Mash distances of conspecific genomes',
                                    'nwk', 'mashtree.nwk', 'Pan-Genome analysis', 'pan-genome', False)

    def prepare_file_upload(self, desc_label, file_format, filename, group_name=None, subdir_name=None):

        obj = {}
        desc = emg_models.DownloadDescriptionLabel \
            .objects.using(self.database) \
            .filter(description_label__iexact=desc_label) \
            .first()
        obj['description'] = desc
        if desc is None:
            logger.error('Desc_label missing: {0}'.format(desc_label))
            quit()

        fmt = emg_models.FileFormat \
            .objects.using(self.database) \
            .filter(format_extension=file_format, compression=False) \
            .first()
        obj['file_format'] = fmt

        name = os.path.basename(filename)
        obj['realname'] = name
        obj['alias'] = name

        if group_name:
            group = emg_models.DownloadGroupType \
                .objects.using(self.database) \
                .filter(group_type=group_name) \
                .first()
            obj['group_type'] = group

        if subdir_name:
            subdir = emg_models.DownloadSubdir \
                .objects.using(self.database) \
                .filter(subdir=subdir_name) \
                .first()
            obj['subdir'] = subdir

        return obj

    def upload_genome_file(self, genome, directory, desc_label, file_format, filename, group_type, subdir,
                           require_existent_and_non_empty):
        defaults = self.prepare_file_upload(desc_label, file_format, filename, group_type, subdir)
        path = os.path.join(directory, subdir, filename)
        if not (os.path.isfile(path) and os.path.getsize(path) > 0):
            if require_existent_and_non_empty:
                raise FileNotFoundError(f"Required file at {path} either missing or empty")
            else:
                logger.warning(f"File not found or empty at {path}. This is allowable, but will not be uploaded.")
                return
        emg_models.GenomeDownload.objects.using(self.database).update_or_create(genome=genome,
                                                                                alias=defaults['alias'],
                                                                                defaults=defaults)

    def upload_catalogue_files(self):
        self.upload_catalogue_file(self.catalogue_obj,
                                 'Phylogenetic tree of catalogue genomes',
                                 'json',
                                 'phylo_tree.json')

    def upload_catalogue_file(self, catalogue, desc_label, file_format, filename):
        defaults = self.prepare_file_upload(desc_label, file_format, filename, None, None)
        emg_models.GenomeCatalogueDownload.objects.using(self.database).update_or_create(
            genome_catalogue=catalogue,
            alias=defaults['alias'],
            defaults=defaults)
