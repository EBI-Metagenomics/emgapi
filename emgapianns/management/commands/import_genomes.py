import logging
import os

from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand
from django.db import IntegrityError

from emgapi import models as emg_models
from ..lib.genome_util import sanity_check_genome_output, \
    sanity_check_release_dir, find_genome_results, \
    get_result_path, read_tsv_w_headers, read_json

logger = logging.getLogger(__name__)

cog_cache = {}
ipr_cache = {}


class Command(BaseCommand):
    obj_list = list()
    rootpath = None
    genome_folders = None
    release_obj = None

    database = None

    def add_arguments(self, parser):
        parser.add_argument('rootpath', action='store', type=str, )
        parser.add_argument('release_version', action='store', type=str)
        parser.add_argument('--database', type=str,
                            default='default')

    def handle(self, *args, **options):
        self.rootpath = os.path.realpath(options.get('rootpath').strip())
        if not os.path.exists(self.rootpath):
            raise FileNotFoundError('Results dir {} does not exist'
                                    .format(self.rootpath))

        release_version = options['release_version'].strip()
        release_dir = os.path.join(self.rootpath, release_version)

        self.release_obj = self.get_release(release_version, release_dir)
        self.database = options['database']

        logger.info("CLI %r" % options)

        genome_dirs = find_genome_results(release_dir)
        logger.debug(
            'Found {} genome dirs to upload'.format(len(genome_dirs)))

        [sanity_check_genome_output(d) for d in genome_dirs]

        sanity_check_release_dir(release_dir)

        for d in genome_dirs:
            self.upload_dir(d)

        self.upload_release_files(release_dir)

    def get_release(self, release_version, result_dir):
        return emg_models.Release.objects.using(
            self.database).get_or_create(release_version=release_version,
                                         result_directory=result_dir)[0]

    def upload_dir(self, d):
        logger.info('Uploading dir: {}'.format(d))
        genome = self.create_genome(d)
        self.set_genome_release(genome)

        self.upload_cog_results(genome, d)
        self.upload_kegg_class_results(genome, d)
        self.upload_kegg_module_results(genome, d)
        self.upload_genome_files(genome)

    def set_genome_release(self, genome):
        self.release_obj.genomes.add(genome)
        genome.releases.add(self.release_obj)

    @staticmethod
    def get_gold_biome(lineage):
        return emg_models.Biome.objects.get(lineage=lineage)

    @staticmethod
    def get_or_create_genome_set(setname):
        return emg_models.GenomeSet.objects.get_or_create(name=setname)[0]

    def prepare_genome_data(self, genome_dir):
        d = read_json(os.path.join(genome_dir, 'genome.json'))

        d['biome'] = self.get_gold_biome(d['gold_biome'])
        d['genome_set'] = self.get_or_create_genome_set(d['genome_set'])
        d.update(d['pangenome'])
        d['geo_origin'] = self.get_geo_location(d['geographic_origin'])

        del d['geographic_origin']
        del d['pangenome']
        del d['gold_biome']
        return d

    def get_geo_location(self, location):
        return emg_models.GeographicLocation \
            .objects.get_or_create(name=location)[0]

    def attach_geo_location(self, genome, location):
        genome.pangenome_geographic_range.add(self.get_geo_location(location))

    def create_genome(self, genome_dir):
        data = self.prepare_genome_data(genome_dir)
        geo_locations = data['geographic_range']
        del data['geographic_range']

        data['result_directory'] = get_result_path(genome_dir)

        g, created = emg_models.Genome.objects.update_or_create(
            accession=data['accession'],
            defaults=data)
        g.save()

        [self.attach_geo_location(g, l) for l in geo_locations]

        return g

    def upload_cog_results(self, genome, d):
        genome_cogs = os.path.join(d, 'genome', 'cog_summary.tsv')
        self.upload_cog_result(genome, genome_cogs, False)
        logger.info('Loaded Genome COG for {}'.format(genome.accession))

        pangenome_cogs = os.path.join(d, 'pan-genome', 'cog_summary.tsv')
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

    def upload_kegg_class_results(self, genome, d):
        genome_kegg_classes = os.path.join(d, 'genome', 'kegg_classes.tsv')
        self.upload_kegg_class_result(genome, genome_kegg_classes, False)
        logger.info(
            'Loaded Genome KEGG classes for {}'.format(genome.accession))

        pangenome_kegg_classes = os.path.join(d, 'pan-genome',
                                              'kegg_classes.tsv')
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
            .get_or_create(genome=genome,
                           kegg_class=kegg_class,
                           defaults=defaults)

        if is_pangenome:
            count.pangenome_count = count_val
        else:
            count.genome_count = count_val

        count.save(using=self.database)

    def upload_kegg_module_results(self, genome, d):
        genome_kegg_modules = os.path.join(d, 'genome', 'kegg_modules.tsv')
        self.upload_kegg_module_result(genome, genome_kegg_modules, False)
        logger.info(
            'Loaded Genome KEGG modules for {}'.format(genome.accession))

        pangenome_kegg_classes = os.path.join(d, 'pan-genome',
                                              'kegg_modules.tsv')
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
            .get_or_create(genome=genome,
                           kegg_module=kegg_module,
                           defaults=defaults)

        if is_pangenome:
            count.pangenome_count = count_val
        else:
            count.genome_count = count_val

        count.save(using=self.database)

    def upload_genome_files(self, genome):
        logger.info('Uploading genome files...')
        # TODO add filepath
        self.upload_genome_file(genome, 'Genome CDS', 'fasta',
                                genome.accession + '.fa')
        self.upload_genome_file(genome, 'Genome Assembly', 'fasta',
                                genome.accession + '.fna')
        self.upload_genome_file(genome, 'EggNOG annotation results', 'tsv',
                                genome.accession + '_eggNOG.tsv')
        self.upload_genome_file(genome, 'InterProScan results', 'tsv',
                                genome.accession + '_InterProScan.tsv')

        self.upload_genome_file(genome, 'Accessory genes', 'fasta',
                                'accessory_genes.faa')
        self.upload_genome_file(genome, 'Core genes', 'fasta',
                                'core_genes.faa')
        self.upload_genome_file(genome, 'Core & Accessory genes', 'fasta',
                                'pan-genome.faa')
        self.upload_genome_file(genome,
                                'EggNOG annotation results (pangenome)', 'tsv',
                                'pan-genome_eggNOG.tsv')
        self.upload_genome_file(genome,
                                'InterProScan annotation results (pangenome)',
                                'tsv', 'pan-genome_InterProScan.tsv')
        self.upload_genome_file(genome,
                                'Gene Presence / Absence matrix (pangenome)',
                                'tsv', 'genes_presence-absence.tsv')

    def prepare_file_upload(self, obj, desc_label, file_format, filename):
        desc = emg_models.DownloadDescriptionLabel \
            .objects.using(self.database) \
            .filter(description_label=desc_label) \
            .first()

        fmt = emg_models.FileFormat \
            .objects.using(self.database) \
            .filter(format_extension=file_format, compression=False) \
            .first()

        name = os.path.basename(filename)
        group = emg_models.DownloadGroupType \
            .objects.using(self.database) \
            .filter(group_type='Genome analysis') \
            .first()
        obj.description = desc
        obj.file_format = fmt
        obj.realname = name
        obj.group_type = group
        obj.alias = name

    def upload_genome_file(self, genome, desc_label, file_format, filename):
        obj = emg_models.GenomeDownload(genome=genome)
        self.prepare_file_upload(obj, desc_label, file_format, filename)
        acc = genome.accession
        try:
            obj.save(using=self.database)
            logger.info('Upload {} file {}'.format(acc, filename))
        except IntegrityError:
            logger.debug(
                '{} was already uploaded for genome {}'.format(filename,
                                                               acc))

    def upload_release_files(self, release_dir):
        self.upload_release_file(self.release_obj,
                                 'Phylogenetic tree',
                                 'json',
                                 'phylo_tree.json')

    def upload_release_file(self, release, desc_label, file_format, filename):
        obj = emg_models.ReleaseDownload(release=release)
        self.prepare_file_upload(obj, desc_label, file_format, filename)
        try:
            obj.save(using=self.database)
            logger.info('Upload {}'.format(filename))
        except IntegrityError:
            vers = release.release_version
            logger.debug(
                '{} was already uploaded for release {} '.format(filename,
                                                                 vers))
