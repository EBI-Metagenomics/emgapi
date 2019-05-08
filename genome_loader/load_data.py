from datetime import datetime
import os
import sys
import logging
import re
import json
import argparse

import django.db
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Q

os.environ['DJANGO_SETTINGS_MODULE'] = 'emgcli.settings'

django.setup()

from emgapi import models

KEGG_ORTHOLOGY = os.path.join(os.path.dirname(__file__), 'kegg_orthology.json')

EXPECTED_FILES = {'accessory_genome_cds.fa', 'cog_counts.tab',
                  'core_genome_cds.fa', 'eggnog_raw.tab', 'eggnog_top10.tab',
                  'genome_cds.fa', 'genome_seq.fa', 'genome_stats.tab',
                  'ipr_raw.tab', 'ipr_top10.tab', 'kegg_counts.tab',
                  'pan_genome_cds.fa'}

cog_cache = {}
ipr_cache = {}
kegg_cache = {}


class GenomePopulator:
    def __init__(self, args):
        self.database = args.database
        if args.reload_kegg:
            self.reload_kegg()
        genomes = os.listdir(args.directory)
        genome_dirs = [os.path.join(args.directory, g) for g in genomes]
        for d in genome_dirs:
            validate_genome_dir(d)

        for d in genome_dirs:
            self.upload_dir(d)

    def reload_kegg(self):
        kegg_data = read_kegg_orthology()
        for kegg_id, kegg_data in kegg_data.items():
            self.save_kegg_entry(kegg_id, kegg_data)

    def save_kegg_entry(self, kegg_id, data):
        name, parent_id = data
        try:
            entry = models.KeggEntry(brite_id=kegg_id,
                                     brite_name=name,
                                     parent=kegg_cache.get(parent_id))
            entry.save(using=self.database)
        except IntegrityError:
            entry = models.KeggEntry.objects\
                .using(self.database)\
                .get(brite_id=kegg_id)

        kegg_cache[kegg_id] = entry

    def upload_dir(self, d):
        genome = self.create_genome_obj(d)
        self.upload_cog_counts(genome, d)
        self.upload_ipr_counts(genome, d)
        self.upload_kegg_counts(genome, d)

    def create_genome_obj(self, genome_dir):
        gs = load_genome_stats(os.path.join(genome_dir, 'genome_stats.tab'))
        g = models.Genome(**gs)
        try:
            g.save(using=self.database)
        except IntegrityError:
            g = models.Genome.objects.using(self.database) \
                .get(accession=gs['accession'])
        return g

    def upload_cog_counts(self, genome_obj, d):
        cog_counts = load_cog_stats(os.path.join(d, 'cog_counts.tab'))
        for cc in cog_counts:
            self.upload_cog_count(genome_obj, cc)

    def upload_cog_count(self, genome, cog_count):
        c_name = cog_count['name']
        cog = self.get_cog_cat(c_name)
        models.GenomeCogCounts(genome=genome, cog=cog,
                               count=int(cog_count['count'])) \
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

    def upload_ipr_counts(self, genome_obj, d):
        ipr_matches = load_ipr_stats(os.path.join(d, 'ipr_top10.tab'))
        for ipr_match in ipr_matches:
            self.upload_ipr_count(genome_obj, ipr_match)

    def upload_ipr_count(self, genome_obj, ipr_match):
        ipr_accession = ipr_match['ipr_accession']
        ipr_entry = self.get_ipr_entry(ipr_accession)
        models.GenomeIprCount(genome=genome_obj,
                              ipr_entry=ipr_entry,
                              count=int(ipr_match['count'])) \
            .save(using=self.database)

    def get_ipr_entry(self, ipr_accession):
        ipr = ipr_cache.get(ipr_accession)
        if not ipr:
            try:
                ipr = models.IprEntry.objects.using(self.database) \
                    .get(accession=ipr_accession)
            except ObjectDoesNotExist:
                ipr = models.IprEntry(accession=ipr_accession)
                ipr.save(using=self.database)
            ipr_cache[ipr_accession] = ipr
        return ipr

    def upload_kegg_counts(self, genome_obj, d):
        kegg_matches = load_kegg_stats(os.path.join(d, 'kegg_counts.tab'))
        for kegg_match in kegg_matches:
            self.upload_kegg_match(genome_obj, kegg_match)

    def get_kegg_entry(self, kegg_id):
        kegg = kegg_cache.get(kegg_id)
        if not kegg:
            try:
                kegg = models.KeggEntry.objects.using(self.database) \
                    .get(brite_id=kegg_id)
            except ObjectDoesNotExist:
                kegg = models.KeggEntry(brite_id=kegg_id)
                kegg.save(using=self.database)
                kegg_cache[kegg_id] = kegg
        return kegg

    def upload_kegg_match(self, genome_obj, kegg_match):
        kegg_id = kegg_match['kegg_id']
        kegg = self.get_kegg_entry(kegg_id)
        models.GenomeKeggCounts(genome=genome_obj,
                                kegg_entry=kegg,
                                count=kegg_match['count'])\
            .save(using=self.database)


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


IPR_HEADERS = ['accession', 'rank', 'ipr_accession', 'count']


def load_ipr_stats(fs):
    with open(fs) as f:
        lines = [l.strip().split('\t') for l in f.readlines()]
    ipr_matches = [dict(zip(IPR_HEADERS, l)) for l in lines]
    return ipr_matches


KEGG_HEADERS = ['accession', 'kegg_id', 'count']


def load_kegg_stats(fs):
    with open(fs) as f:
        lines = [l.strip().split('\t') for l in f.readlines()]
    kegg_matches = [dict(zip(KEGG_HEADERS, l)) for l in lines]
    return kegg_matches


def validate_genome_dir(d):
    fs = set(os.listdir(d))
    if len(EXPECTED_FILES.difference(fs)):
        missing_files = ", ".join(EXPECTED_FILES.difference(fs))
        raise ValueError(
            'Files are missing from directory {}: {}'.format(d, missing_files))


def read_kegg_orthology():
    with open(KEGG_ORTHOLOGY) as f:
        kegg = json.load(f)
    entries = {}

    def find_nodes(node, parent_id=None, depth=0):
        match = re.findall('^([^K]\d+) ([^[]*)', node['name'])
        if len(match) > 0:
            node_id, node_name = match[0]
            if node_id not in entries:
                entries[node_id] = [node_name, parent_id]

            children = node.get('children') or []
            for child in children:
                find_nodes(child, parent_id=node_id, depth=depth + 1)

    for child_node in kegg['children']:
        find_nodes(child_node)
    return entries


def parse_args():
    parser = argparse.ArgumentParser(
        description='Tool to populate emg database with latest set of genomes')
    parser.add_argument('-db', '--database', help='Target django database',
                        default='default')
    parser.add_argument('--reload-kegg',
                        help='Download full kegg orthology and load BRITE to db',
                        action='store_true')
    parser.add_argument('-d', '--directory',
                        help='Directory containing genome output', default='.')
    return parser.parse_args()


def main():
    args = parse_args()
    GenomePopulator(args)


if __name__ == '__main__':
    main()
