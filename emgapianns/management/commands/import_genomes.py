import logging
import os

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
        parser.add_argument('version', action='store', type=str)
        parser.add_argument('--database', type=str,
                            default='default')

    def handle(self, *args, **options):
        self.rootpath = os.path.realpath(options.get('rootpath').strip())
        if not os.path.exists(self.rootpath):
            raise FileNotFoundError('Results dir {} does not exist'
                                    .format(self.rootpath))

        version = options['version'].strip()
        release_dir = os.path.join(self.rootpath, version)

        self.database = options['database']
        self.release_obj = self.get_release(version, release_dir)

        logger.info("CLI %r" % options)

        genome_dirs = find_genome_results(release_dir)
        logger.debug(
            'Found {} genome dirs to upload'.format(len(genome_dirs)))

        [sanity_check_genome_output(d) for d in genome_dirs]

        sanity_check_release_dir(release_dir)

        for d in genome_dirs:
            self.upload_dir(d)

        self.upload_release_files()

    def get_release(self, version, result_dir):
        base_result_dir = get_result_path(result_dir)
        return emg_models.Release.objects \
            .using(self.database) \
            .get_or_create(version=version,
                           result_directory=base_result_dir)[0]

    def upload_dir(self, d):
        logger.info('Uploading dir: {}'.format(d))
        genome, has_pangenome = self.create_genome(d)
        self.set_genome_release(genome)

        self.upload_cog_results(genome, d, has_pangenome)
        self.upload_kegg_class_results(genome, d, has_pangenome)
        self.upload_kegg_module_results(genome, d, has_pangenome)
        self.upload_genome_files(genome, has_pangenome)

    def set_genome_release(self, genome):
        try:
            emg_models.ReleaseGenomes(release=self.release_obj, genome=genome).save(using=self.database)
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

        data['result_directory'] = '/genomes/{}'.format(self.release_obj.version) + get_result_path(genome_dir)

        # TODO: remove after Alex A. regenerates the genomes files.
        gtype = data.get('genome_set', None)
        if gtype and gtype.name == 'PATRIC/IMG' and 'genome_accession' in data:
            ga = data.pop('genome_accession')
            if '.' in ga:
                data['patric_genome_accession'] = ga
            else:
                data['img_genome_accession'] = ga

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

    def upload_genome_files(self, genome, has_pangenome):
        logger.info('Uploading genome files...')
        self.upload_genome_file(genome, 'Predicted CDS', 'fasta',
                                genome.accession + '.faa', 'Genome analysis', 'genome')
        self.upload_genome_file(genome, 'Nucleic Acid Sequence', 'fasta',
                                genome.accession + '.fna', 'Genome analysis', 'genome')
        self.upload_genome_file(genome, 'Nucleic Acid Sequence index', 'fai',
                                genome.accession + '.fna.fai', 'Genome analysis', 'genome')
        self.upload_genome_file(genome, 'Genome Annotation', 'gff',
                                genome.accession + '.gff', 'Genome analysis', 'genome')
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

    def upload_release_files(self):
        self.upload_release_file(self.release_obj,
                                 'Phylogenetic tree of release genomes',
                                 'json',
                                 'phylo_tree.json')

    def upload_release_file(self, release, desc_label, file_format, filename):
        defaults = self.prepare_file_upload(desc_label, file_format, filename, None, None)
        emg_models.ReleaseDownload.objects.using(self.database).update_or_create(release=release,
                                                                                 alias=defaults['alias'],
                                                                                 defaults=defaults)
