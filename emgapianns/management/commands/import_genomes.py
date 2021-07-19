import logging
import os

from django.core.management import BaseCommand
from django.db import IntegrityError
from emgapi import models as emg_models

from ..lib.genome_util import sanity_check_genome_output, \
    sanity_check_catalogue_dir, find_genome_results, \
    get_result_path, read_tsv_w_headers, read_json

logger = logging.getLogger(__name__)

cog_cache = {}
ipr_cache = {}


class Command(BaseCommand):
    obj_list = list()
    rootpath = None
    genome_folders = None
    catalogue_obj = None
    catalogue_dir = None

    database = None

    def add_arguments(self, parser):
        parser.add_argument('rootpath', action='store', type=str, )
        # parser.add_argument('version', action='store', type=str)
        parser.add_argument('catalogue_series_id', action='store', type=str)
        parser.add_argument('catalogue_version', action='store', type=str)
        parser.add_argument('--database', type=str,
                            default='default')

    def handle(self, *args, **options):
        self.rootpath = os.path.realpath(options.get('rootpath').strip())
        if not os.path.exists(self.rootpath):
            raise FileNotFoundError('Results dir {} does not exist'
                                    .format(self.rootpath))

        series = options['catalogue_series_id'].strip()
        version = options['catalogue_version'].strip()
        self.catalogue_dir = os.path.join(self.rootpath, series, version)

        self.database = options['database']
        self.catalogue_obj = self.get_catalogue()

        logger.info("CLI %r" % options)

        genome_dirs = find_genome_results(self.catalogue_dir)
        logger.debug(
            'Found {} genome dirs to upload'.format(len(genome_dirs)))

        [sanity_check_genome_output(d) for d in genome_dirs]

        sanity_check_catalogue_dir(self.catalogue_dir)

        for d in genome_dirs:
            self.upload_dir(d)

        self.upload_catalogue_files()

    def get_catalogue(self, catalogue_series_id, catalogue_version, result_dir):
        base_result_dir = get_result_path(result_dir)
        series, _ = emg_models.GenomeCatalogueSeries.objects\
            .using(self.database)\
            .get_or_create(catalogue_series_id=catalogue_series_id,
                           defaults={'name': catalogue_series_id})
        catalogue, _ = emg_models.GenomeCatalogue.objects \
            .using(self.database) \
            .get_or_create(
                version=catalogue_version,
                catalogue_series=series,
                defaults={
                    'name': '{0} v{1}'.format(catalogue_series_id, catalogue_version),
                    'result_directory': base_result_dir
                })
        return catalogue

    def upload_dir(self, directory):
        logger.info('Uploading dir: {}'.format(directory))
        genome, has_pangenome = self.create_genome(directory)
        self.set_genome_catalogue(genome)

        self.upload_cog_results(genome, directory, has_pangenome)
        self.upload_kegg_class_results(genome, directory, has_pangenome)
        self.upload_kegg_module_results(genome, directory, has_pangenome)
        self.upload_antismash_geneclusters(genome, directory)
        self.upload_genome_files(genome, has_pangenome)

    def set_genome_catalogue(self, genome):
        try:
            genome.catalogues.add(genome_catalogue=self.catalogue_obj).save(using=self.database)
        except IntegrityError:
            pass

    def get_gold_biome(self, lineage):
        return emg_models.Biome.objects.using(self.database).get(lineage=lineage)

    def get_or_create_genome_set(self, setname):
        return emg_models.GenomeSet.objects.using(self.database).get_or_create(name=setname)[0]

    def prepare_genome_data(self, genome_dir):
        d = read_json(os.path.join(genome_dir, 'genome.json'))

        has_pangenome = 'pangenome' in d
        d['biome'] = self.get_gold_biome(d['gold_biome'])
        d['genome_set'] = self.get_or_create_genome_set(d['genome_set'])
        if has_pangenome:
            d.update(d['pangenome'])
            del d['pangenome']

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

        data['result_directory'] = self.catalogue_dir + get_result_path(genome_dir)

        g, created = emg_models.Genome.objects.using(self.database).update_or_create(
            accession=data['accession'],
            defaults=data)
        g.save(using=self.database)

        if geo_locations:
            [self.attach_geo_location(g, l) for l in geo_locations]

        return g, has_pangenome

    def upload_cog_results(self, genome, d, has_pangenome):
        genome_cogs = os.path.join(d, 'genome', 'cog_summary.tsv')
        self.upload_cog_result(genome, genome_cogs, False)
        logger.info('Loaded Genome COG for {}'.format(genome.accession))

        pangenome_cogs = os.path.join(d, 'pan-genome', 'cog_summary.tsv')
        if has_pangenome:
            self.upload_cog_result(genome, pangenome_cogs, True)
            logger.info('Loaded PanGenome COG for {}'.format(genome.accession))

    def upload_cog_result(self, genome, f, is_pangenome):
        counts = read_tsv_w_headers(f)
        for cc in counts:
            self.upload_cog_count(genome, cc, is_pangenome)
        logger.info('Loaded Genome COG for {}'.format(genome.accession))

    def upload_cog_count(self, genome, cog_count, is_pangenome):
        c_name = cog_count['COG_category']
        cog = self.get_cog_cat(c_name)

        count_val = int(cog_count['Counts'])

        defaults = {'genome_count': 0, 'pangenome_count': 0}

        count, created = emg_models.GenomeCogCounts.objects \
            .using(self.database) \
            .get_or_create(genome=genome,
                           cog=cog,
                           defaults=defaults)
        if is_pangenome:
            count.pangenome_count = count_val
        else:
            count.genome_count = count_val
        count.save(using=self.database)

    def get_cog_cat(self, c_name):
        return emg_models.CogCat.objects.using(self.database) \
            .get_or_create(name=c_name)[0]

    def upload_kegg_class_results(self, genome, d, has_pangenome):
        genome_kegg_classes = os.path.join(d, 'genome', 'kegg_classes.tsv')
        self.upload_kegg_class_result(genome, genome_kegg_classes, False)
        logger.info(
            'Loaded Genome KEGG classes for {}'.format(genome.accession))

        pangenome_kegg_classes = os.path.join(d, 'pan-genome',
                                              'kegg_classes.tsv')
        if has_pangenome:
            self.upload_kegg_class_result(genome, pangenome_kegg_classes, True)
            logger.info(
                'Loaded PanGenome KEGG classes for {}'.format(genome.accession))

    def upload_kegg_class_result(self, genome, f, pangenome):
        kegg_matches = read_tsv_w_headers(f)
        for kegg_match in kegg_matches:
            self.upload_kegg_class_count(genome, kegg_match, pangenome)

    def get_kegg_class(self, kegg_cls_id):
        return emg_models.KeggClass.objects.using(self.database) \
            .get_or_create(class_id=kegg_cls_id)[0]

    def upload_kegg_class_count(self, genome, kegg_match, is_pangenome):
        kegg_id = kegg_match['KEGG_class']
        kegg_class = self.get_kegg_class(kegg_id)

        count_val = int(kegg_match['Counts'])

        defaults = {'genome_count': 0, 'pangenome_count': 0}

        count, created = emg_models.GenomeKeggClassCounts.objects \
            .using(self.database) \
            .get_or_create(genome=genome,
                           kegg_class=kegg_class,
                           defaults=defaults)

        if is_pangenome:
            count.pangenome_count = count_val
        else:
            count.genome_count = count_val

        count.save(using=self.database)

    def upload_kegg_module_results(self, genome, d, has_pangenome):
        genome_kegg_modules = os.path.join(d, 'genome', 'kegg_modules.tsv')
        self.upload_kegg_module_result(genome, genome_kegg_modules, False)
        logger.info(
            'Loaded Genome KEGG modules for {}'.format(genome.accession))

        pangenome_kegg_classes = os.path.join(d, 'pan-genome',
                                              'kegg_modules.tsv')
        if has_pangenome:
            self.upload_kegg_module_result(genome, pangenome_kegg_classes, True)
            logger.info(
                'Loaded PanGenome KEGG modules for {}'.format(genome.accession))

    def upload_kegg_module_result(self, genome, f, is_pangenome):
        kegg_matches = read_tsv_w_headers(f)
        for kegg_match in kegg_matches:
            self.upload_kegg_module_count(genome, kegg_match, is_pangenome)

    def get_kegg_module(self, name):
        return emg_models.KeggModule.objects.using(self.database) \
            .get_or_create(name=name)[0]

    def upload_kegg_module_count(self, genome, kegg_match, is_pangenome):
        kegg_module_id = kegg_match['KEGG_module']
        kegg_module = self.get_kegg_module(kegg_module_id)

        count_val = int(kegg_match['Counts'])

        defaults = {'genome_count': 0, 'pangenome_count': 0}

        count, created = emg_models.GenomeKeggModuleCounts.objects \
            .using(self.database) \
            .get_or_create(genome=genome,
                           kegg_module=kegg_module,
                           defaults=defaults)

        if is_pangenome:
            count.pangenome_count = count_val
        else:
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

    def upload_genome_files(self, genome, has_pangenome):
        logger.info('Uploading genome files...')
        self.upload_genome_file(genome, 'Predicted CDS (aa)', 'fasta',
                                genome.accession + '.faa', 'Genome analysis', 'genome')
        self.upload_genome_file(genome, 'Nucleic Acid Sequence', 'fasta',
                                genome.accession + '.fna', 'Genome analysis', 'genome')
        self.upload_genome_file(genome, 'Nucleic Acid Sequence index', 'fai',
                                genome.accession + '.fna.fai', 'Genome analysis', 'genome')
        self.upload_genome_file(genome, 'Genome Annotation', 'gff',
                                genome.accession + '.gff', 'Genome analysis', 'genome')
        self.upload_genome_file(genome, 'Genome antiSMASH Annotation', 'gff',
                                genome.accession + '_antismash.gff', 'Genome analysis', 'genome')
        self.upload_genome_file(genome, 'EggNog annotation', 'tsv',
                                genome.accession + '_eggNOG.tsv', 'Genome analysis', 'genome')
        self.upload_genome_file(genome, 'InterProScan annotation', 'tsv',
                                genome.accession + '_InterProScan.tsv', 'Genome analysis', 'genome')

        if has_pangenome:
            self.upload_genome_file(genome, 'Accessory predicted CDS', 'fasta',
                                    'accessory_genes.faa', 'Pan-Genome analysis', 'pan-genome')
            self.upload_genome_file(genome, 'Core predicted CDS', 'fasta',
                                    'core_genes.faa', 'Pan-Genome analysis', 'pan-genome')
            self.upload_genome_file(genome, 'Core & Accessory predicted CDS', 'fasta',
                                    'pan-genome.faa', 'Pan-Genome analysis', 'pan-genome')
            self.upload_genome_file(genome,
                                    'EggNog annotation (core and accessory)', 'tsv',
                                    'pan-genome_eggNOG.tsv', 'Pan-Genome analysis', 'pan-genome')
            self.upload_genome_file(genome,
                                    'InterProScan annotation (core and accessory)',
                                    'tsv', 'pan-genome_InterProScan.tsv', 'Pan-Genome analysis', 'pan-genome')
            self.upload_genome_file(genome,
                                    'Gene Presence / Absence matrix',
                                    'tsv', 'genes_presence-absence.tsv', 'Pan-Genome analysis', 'pan-genome')
            self.upload_genome_file(genome,
                                    'Pairwise Mash distances of conspecific genomes',
                                    'nwk', 'mashtree.nwk ', 'Pan-Genome analysis', 'pan-genome')

    def prepare_file_upload(self, desc_label, file_format, filename, group_name=None, subdir_name=None):

        obj = {}
        desc = emg_models.DownloadDescriptionLabel \
            .objects.using(self.database) \
            .filter(description_label=desc_label) \
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

    def upload_genome_file(self, genome, desc_label, file_format, filename, group_type, subdir):
        defaults = self.prepare_file_upload(desc_label, file_format, filename, group_type, subdir)
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
