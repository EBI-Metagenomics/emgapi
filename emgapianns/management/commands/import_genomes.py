import logging
import os

from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand
from django.db import IntegrityError

from emgapi import models as emg_models
from ..lib.genome_util import sanity_check_result_dirs, load_genome_stats, \
    load_ipr_stats, load_kegg_stats, load_cog_stats, find_results, \
    get_result_path

logger = logging.getLogger(__name__)

cog_cache = {}
ipr_cache = {}
kegg_cache = {}


class Command(BaseCommand):
    obj_list = list()
    rootpath = None
    genome_folders = None
    release_version = None
    download_descriptions = emg_models.DownloadDescriptionLabel.objects.all()
    download_groups = emg_models.DownloadGroupType.objects.all()
    file_formats = emg_models.FileFormat.objects.all()

    def add_arguments(self, parser):
        parser.add_argument('rootpath', action='store', type=str, )
        parser.add_argument('release_version', action='store', type=str, )

    def handle(self, *args, **options):
        self.rootpath = options.get('rootpath')
        self.release_version = options.get('release_version')
        logger.info("CLI %r" % options)
        release_dir = os.path.join(self.rootpath, self.release_version)

        results = find_results(release_dir)

        sanity_check_result_dirs(results)

        for d in results:
            self.upload_dir(d)

    def upload_dir(self, d):
        genome = self.create_genome(d)
        self.upload_cog_counts(genome, d)
        self.upload_ipr_counts(genome, d)
        self.upload_kegg_counts(genome, d)
        self.upload_files(genome)

    def create_genome(self, genome_dir):
        gs = load_genome_stats(os.path.join(genome_dir, 'genome_stats.tab'))
        g = emg_models.Genome(**gs)
        g.result_directory = get_result_path(genome_dir)
        try:
            g.save()
            logger.info('Created genome {}'.format(g.accession))
        except IntegrityError:
            g = emg_models.Genome.objects.get(accession=gs['accession'])
            logger.warning('Genome {} already exists'.format(g.accession))
        return g

    def upload_cog_counts(self, genome, d):
        cog_counts = load_cog_stats(os.path.join(d, 'cog_counts.tab'))
        for cc in cog_counts:
            self.upload_cog_count(genome, cc)
        logger.info('Loaded COG for {}'.format(genome.accession))

    def upload_cog_count(self, genome, cog_count):
        c_name = cog_count['name']
        cog = self.get_cog_cat(c_name)
        try:
            emg_models.GenomeCogCounts(genome=genome, cog=cog,
                                       count=int(cog_count['count'])).save()
        except IntegrityError:
            logger.warning('Cog entry for {} already exists'.format(
                genome.accession))

    def get_cog_cat(self, c_name):
        cog = cog_cache.get(c_name)
        if not cog:
            try:
                cog = emg_models.CogCat.objects.get(name=c_name)
            except ObjectDoesNotExist:
                cog = emg_models.CogCat(name=c_name)
                cog.save()
            cog_cache[c_name] = cog
        return cog

    def upload_ipr_counts(self, genome, d):
        ipr_matches = load_ipr_stats(os.path.join(d, 'ipr_top10.tab'))
        for ipr_match in ipr_matches:
            self.upload_ipr_count(genome, ipr_match)
        logger.info('Loaded IPR for {}'.format(genome.accession))

    def upload_ipr_count(self, genome, ipr_match):
        ipr_accession = ipr_match['ipr_accession']
        ipr_entry = self.get_ipr_entry(ipr_accession)
        try:
            emg_models.GenomeIprCount(genome=genome,
                                      ipr_entry=ipr_entry,
                                      count=int(ipr_match['count'])).save()
        except IntegrityError:
            logger.warning('IPR entry for {} already exists'.format(
                genome.accession))

    def get_ipr_entry(self, ipr_accession):
        ipr = ipr_cache.get(ipr_accession)
        if not ipr:
            try:
                ipr = emg_models.IprEntry.objects.get(accession=ipr_accession)
            except ObjectDoesNotExist:
                ipr = emg_models.IprEntry(accession=ipr_accession)
                ipr.save()
            ipr_cache[ipr_accession] = ipr
        return ipr

    def upload_kegg_counts(self, genome, d):
        kegg_matches = load_kegg_stats(os.path.join(d, 'kegg_counts.tab'))
        for kegg_match in kegg_matches:
            self.upload_kegg_match(genome, kegg_match)
        logger.info('Loaded KEGG for {}'.format(genome.accession))

    def get_kegg_entry(self, kegg_id):
        kegg = kegg_cache.get(kegg_id)
        if not kegg:
            try:
                kegg = emg_models.KeggEntry.objects.get(brite_id=kegg_id)
            except ObjectDoesNotExist:
                kegg = emg_models.KeggEntry(brite_id=kegg_id)
                kegg.save()
                kegg_cache[kegg_id] = kegg
        return kegg

    def upload_kegg_match(self, genome, kegg_match):
        kegg_id = kegg_match['kegg_id']
        kegg = self.get_kegg_entry(kegg_id)
        try:
            emg_models.GenomeKeggCounts(genome=genome, kegg_entry=kegg,
                                        count=kegg_match['count']).save()
        except IntegrityError:
            logger.warning('Kegg entry for {} already exists'.format(
                genome.accession))

    def upload_files(self, genome):
        self.upload_file(genome, 'Genome CDS', 'fasta', 'genome_cds.fa')
        self.upload_file(genome, 'Genome SEQ', 'fasta', 'genome_seq.fa')
        self.upload_file(genome, 'Protein sequence (full)', 'fasta',
                         'pan_genome_cds.fa')
        self.upload_file(genome, 'Protein sequence (accessory)', 'fasta',
                         'accessory_genome_cds.fa')
        self.upload_file(genome, 'Protein sequence (core)', 'fasta',
                         'core_genome_cds.fa')
        self.upload_file(genome, 'Raw output of eggNOG-mapper', 'tab',
                         'eggnog_raw.tab')
        self.upload_file(genome, 'Raw output of InterProScan', 'tab',
                         'ipr_raw.tab')

    def upload_file(self, genome, desc_label, file_format, filename):
        desc = self.download_descriptions \
            .filter(description_label=desc_label) \
            .first()
        fmt = self.file_formats \
            .filter(format_extension=file_format, compression=False).first()
        name = os.path.basename(filename)
        group = self.download_groups \
            .filter(group_type='Genome analysis') \
            .first()
        try:
            emg_models.GenomeDownload(genome=genome,
                                      description=desc,
                                      group_type=group,
                                      file_format=fmt,
                                      realname=name,
                                      alias=name,
                                      release_version=self.release_version)\
                .save()
        except IntegrityError:
            logger.warning(
                '{} was already uploaded for genome'.format(name,
                                                            genome.accession))
