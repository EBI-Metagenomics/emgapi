import logging
import os

from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand
from django.db import IntegrityError

from emgapi import models as emg_models
from ..lib.genome_util import sanity_check_genome_dirs, \
    sanity_check_release_dir, find_genome_results, \
    get_result_path, read_csv_w_headers, read_json

logger = logging.getLogger(__name__)

cog_cache = {}
ipr_cache = {}
kegg_cache = {}


class Command(BaseCommand):
    obj_list = list()
    rootpath = None
    genome_folders = None
    release_obj = None
    download_descriptions = emg_models.DownloadDescriptionLabel.objects.all()
    download_groups = emg_models.DownloadGroupType.objects.all()
    file_formats = emg_models.FileFormat.objects.all()

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
        logging.debug(
            'Found {} genome dirs to upload'.format(len(genome_dirs)))

        sanity_check_genome_dirs(genome_dirs)

        sanity_check_release_dir(release_dir)

        for d in genome_dirs:
            self.upload_dir(d)

        self.upload_release_files(release_dir)

    def get_release(self, release_version, result_dir):
        return emg_models.Release.objects.using(
            self.database).get_or_create(release_version=release_version,
                                         result_directory=result_dir)[0]

    def upload_dir(self, d):
        logger.debug('Uploading dir: {}'.format(d))
        genome = self.create_genome(d)
        self.set_genome_release(genome)

        self.upload_cog_counts(genome, d)
        self.upload_ipr_counts(genome, d)
        self.upload_kegg_counts(genome, d)
        self.upload_eggnog_counts(genome, d)
        self.upload_genome_files(genome)

    def set_genome_release(self, genome):
        try:
            emg_models.ReleaseGenomes(genome=genome, release=self.release_obj) \
                .save(using=self.database)
        except IntegrityError:
            pass

    def create_genome(self, genome_dir):
        gs = read_json(os.path.join(genome_dir, 'genome_stats.json'))
        g = emg_models.Genome(**gs)
        g.result_directory = get_result_path(genome_dir)
        try:
            g.save(using=self.database)
            logger.info('Created genome {}'.format(g.accession))
        except IntegrityError:
            g = emg_models.Genome.objects.using(self.database).get(
                accession=gs['accession'])
            logger.debug('Genome {} already exists'.format(g.accession))
        return g

    def upload_cog_counts(self, genome, d):
        cog_counts = read_csv_w_headers(os.path.join(d, 'cog_counts.csv'))
        for cc in cog_counts:
            self.upload_cog_count(genome, cc)
        logger.info('Loaded COG for {}'.format(genome.accession))

    def upload_cog_count(self, genome, cog_count):
        c_name = cog_count['name']
        cog = self.get_cog_cat(c_name)
        try:
            emg_models.GenomeCogCounts(genome=genome, cog=cog,
                                       count=int(cog_count['count'])).save(
                using=self.database)
        except IntegrityError:
            logger.debug('Cog entry for {} already exists'.format(
                genome.accession))

    def get_cog_cat(self, c_name):
        cog = cog_cache.get(c_name)
        if not cog:
            try:
                cog = emg_models.CogCat.objects.using(self.database).get(
                    name=c_name)
            except ObjectDoesNotExist:
                cog = emg_models.CogCat(name=c_name)
                cog.save(using=self.database)
            cog_cache[c_name] = cog
        return cog

    def upload_ipr_counts(self, genome, results_dir):
        ipr_matches = read_csv_w_headers(
            os.path.join(results_dir, 'ipr_top10.csv'))
        for ipr_match in ipr_matches:
            self.upload_ipr_count(genome, ipr_match)
        logger.info('Loaded IPR for {}'.format(genome.accession))

    def upload_ipr_count(self, genome, ipr_match):
        ipr_accession = ipr_match['ipr_accession']
        ipr_entry = self.get_ipr_entry(ipr_accession)
        try:
            emg_models.GenomeIprCount(genome=genome,
                                      ipr_entry=ipr_entry,
                                      count=int(ipr_match['count'])).save(
                using=self.database)
        except IntegrityError:
            logger.debug('IPR entry for {} already exists'.format(
                genome.accession))

    def get_ipr_entry(self, ipr_accession):
        ipr = ipr_cache.get(ipr_accession)
        if not ipr:
            try:
                ipr = emg_models.IprEntry.objects \
                    .using(self.database) \
                    .get(accession=ipr_accession)
            except ObjectDoesNotExist:
                ipr = emg_models.IprEntry(accession=ipr_accession)
                ipr.save(using=self.database)
            ipr_cache[ipr_accession] = ipr
        return ipr

    def upload_kegg_counts(self, genome, results_dir):
        kegg_matches = read_csv_w_headers(
            os.path.join(results_dir, 'kegg_counts.csv'))
        for kegg_match in kegg_matches:
            self.upload_kegg_match(genome, kegg_match)
        logger.info('Loaded KEGG for {}'.format(genome.accession))

    def get_kegg_entry(self, kegg_id):
        kegg = kegg_cache.get(kegg_id)
        if not kegg:
            try:
                kegg = emg_models.KeggEntry.objects \
                    .using(self.database) \
                    .get(brite_id=kegg_id)
            except ObjectDoesNotExist:
                kegg = emg_models.KeggEntry(brite_id=kegg_id)
                kegg.save(using=self.database)
                kegg_cache[kegg_id] = kegg
        return kegg

    def upload_kegg_match(self, genome, kegg_match):
        kegg_id = kegg_match['kegg_brite']
        kegg = self.get_kegg_entry(kegg_id)
        try:
            emg_models.GenomeKeggCounts(genome=genome,
                                        kegg_entry=kegg,
                                        count=kegg_match['count']) \
                .save(using=self.database)
        except IntegrityError:
            logger.debug('Kegg entry for {} already exists'.format(
                genome.accession))

    def upload_eggnog_counts(self, genome, results_dir):
        eggnog_matches = read_csv_w_headers(
            os.path.join(results_dir, 'eggnog_top10.csv'))
        for eggnog_match in eggnog_matches:
            self.upload_eggnog_match(genome, eggnog_match)
        logger.info('Loaded EggNog for {}'.format(genome.accession))

    def get_eggnog_entry(self, eggnog_organism, eggnog_host,
                         eggnog_description):
        try:
            eggnog = emg_models.EggNogEntry.objects \
                .using(self.database).get(
                organism=eggnog_organism,
                host=eggnog_host,
                description=eggnog_description)
        except ObjectDoesNotExist:
            eggnog = emg_models.EggNogEntry(organism=eggnog_organism,
                                            host=eggnog_host,
                                            description=eggnog_description)
            eggnog.save(using=self.database)
        return eggnog

    def upload_eggnog_match(self, genome, eggnog_match):
        org = eggnog_match['eggnog_organism']
        host = eggnog_match['eggnog_host']
        description = eggnog_match['eggnog_desc']
        kegg = self.get_eggnog_entry(org, host, description)
        try:
            emg_models.GenomeEggNogCounts(genome=genome, eggnog=kegg,
                                          count=eggnog_match['count']) \
                .save(using=self.database)
        except IntegrityError:
            logger.debug(
                'Eggnog entry for {}, {}, {}, {} already exists'.format(
                    genome.accession, org, host, description))

    def upload_genome_files(self, genome):
        self.upload_genome_file(genome, 'Genome CDS', 'fasta', 'genome_cds.fa')
        self.upload_genome_file(genome, 'Genome SEQ', 'fasta', 'genome_seq.fa')
        self.upload_genome_file(genome, 'Protein sequence (full)', 'fasta',
                                'pan_genome_cds.fa')
        self.upload_genome_file(genome, 'Protein sequence (accessory)',
                                'fasta',
                                'accessory_genome_cds.fa')
        self.upload_genome_file(genome, 'Protein sequence (core)', 'fasta',
                                'core_genome_cds.fa')
        self.upload_genome_file(genome, 'Raw output of eggNOG-mapper', 'tab',
                                'eggnog_raw.tab')
        self.upload_genome_file(genome, 'Raw output of InterProScan', 'tab',
                                'ipr_raw.tab')
        self.upload_genome_file(genome, 'Genome GFF', 'gff',
                                'genome.gff')

    def prepare_file_upload(self, obj, desc_label, file_format, filename):
        desc = self.download_descriptions.using(self.database) \
            .filter(description_label=desc_label) \
            .first()
        fmt = self.file_formats.using(self.database) \
            .filter(format_extension=file_format, compression=False).first()
        name = os.path.basename(filename)
        group = self.download_groups.using(self.database) \
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
        try:
            obj.save(using=self.database)
        except IntegrityError:
            acc = genome.accession
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
        except IntegrityError:
            vers = release.release_version
            logger.debug(
                '{} was already uploaded for release {} '.format(filename,
                                                                 vers))
