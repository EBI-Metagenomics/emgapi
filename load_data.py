from datetime import datetime
import os
import sys
import logging
import re
import argparse

import django.db
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Q

os.environ['DJANGO_SETTINGS_MODULE'] = 'emgcli.settings'

django.setup()

from emgapi import models

EXPECTED_FILES = {'accessory_genome_cds.fa', 'cog_counts.tab',
                  'core_genome_cds.fa', 'eggnog_raw.tab', 'eggnog_top10.tab',
                  'genome_cds.fa', 'genome_seq.fa', 'genome_stats.tab',
                  'ipr_raw.tab', 'ipr_top10.tab', 'kegg_counts.tab',
                  'pan_genome_cds.fa'}

cog_cache = {}


class GenomePopulator():
    def __init__(self, args):
        self.database = args.database
        genomes = os.listdir(args.directory)
        genome_dirs = [os.path.join(args.directory, g) for g in genomes]
        for d in genome_dirs:
            validate_genome_dir(d)

        for d in genome_dirs:
            self.upload_dir(d)

    def upload_dir(self, d):
        genome = self.create_genome_obj(d)
        print(genome)
        self.upload_cogs(genome, d)

    def create_genome_obj(self, genome_dir):
        gs = load_genome_stats(os.path.join(genome_dir, 'genome_stats.tab'))
        g = models.Genome(**gs)
        try:
            g.save(using=self.database)
        except IntegrityError:
            g = models.Genome.objects.using(self.database) \
                .get(accession=gs['accession'])
        return g

    def upload_cogs(self, genome_obj, d):
        cog_counts = load_cog_stats(os.path.join(d, 'cog_counts.tab'))
        for cc in cog_counts:
            self.upload_cog_count(genome_obj, cc)

    def upload_cog_count(self, genome, cog_count):
        c_name = cog_count['name']
        cog = self.get_cog_cat(c_name)
        models \
            .CogCounts(genome=genome, cog=cog, count=int(cog_count['count'])) \
            .save(using=self.database)

    def get_cog_cat(self, c_name):
        cog = cog_cache.get(c_name)
        if not cog:
            try:
                cog = models.CogCat.objects.using(self.database) \
                    .get(name=c_name)
            except ObjectDoesNotExist:
                cog = models.CogCat(name=c_name)
                cog.save(using=self.database)
            cog_cache[c_name] = cog
        return cog


GENOME_STATS_HEADERS = ['accession', 'length', 'num_contigs', 'n_50',
                        'gc_content', 'type', 'completeness',
                        'contamination', 'rna_5s', 'rna_16s', 'rna_23s',
                        'trnas', 'num_genomes', 'num_proteins',
                        'pangenome_size', 'core_prop', 'accessory_prop',
                        'eggnog_prop', 'ipr_prop']


def load_genome_stats(fs):
    with open(fs) as f:
        l = f.read().strip().split('\t')
    return dict(zip(GENOME_STATS_HEADERS, l))


COG_HEADERS = ['accession', 'name', 'count']


def load_cog_stats(fs):
    with open(fs) as f:
        lines = [l.strip().split('\t') for l in f.readlines()]
    cog_counts = [dict(zip(COG_HEADERS, l)) for l in lines]
    return cog_counts


def validate_genome_dir(d):
    fs = set(os.listdir(d))
    if len(EXPECTED_FILES.difference(fs)):
        missing_files = ", ".join(EXPECTED_FILES.difference(fs))
        raise ValueError(
            'Files are missing from directory {}: {}'.format(d, missing_files))


def parse_args():
    parser = argparse.ArgumentParser(
        description='Tool to populate emg database with latest set of genomes')
    parser.add_argument('-db', '--database', help='Target django database',
                        default='default')
    parser.add_argument('-d', '--directory',
                        help='Directory containing genome output', default='.')
    return parser.parse_args()


def main():
    args = parse_args()
    GenomePopulator(args)


if __name__ == '__main__':
    main()
