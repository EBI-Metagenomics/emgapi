# import os
# import re
# import json
# import argparse
#
# import django.db
# from django.db import IntegrityError
#
# os.environ['DJANGO_SETTINGS_MODULE'] = 'emgcli.settings'
#
# django.setup()
#
# from emgapi import models
#
# KEGG_ORTHOLOGY = os.path.join(os.path.dirname(__file__), 'kegg_orthology.json')
#
# EXPECTED_FILES = {'accessory_genome_cds.fa', 'cog_counts.tab',
#                   'core_genome_cds.fa', 'eggnog_raw.tab', 'eggnog_top10.tab',
#                   'genome_cds.fa', 'genome_seq.fa', 'genome_stats.tab',
#                   'ipr_raw.tab', 'ipr_top10.tab', 'kegg_counts.tab',
#                   'pan_genome_cds.fa'}
#
# cog_cache = {}
# ipr_cache = {}
# kegg_cache = {}
#
#
# class GenomePopulator:
#     def __init__(self, args):
#         self.database = args.database
#         if args.reload_kegg:
#             self.reload_kegg()
#         genomes = os.listdir(args.directory)
#         genome_dirs = [os.path.join(args.directory, g) for g in genomes]
#         for d in genome_dirs:
#             validate_genome_dir(d)
#
#         for d in genome_dirs:
#             self.upload_dir(d)
#
#     def reload_kegg(self):
#         kegg_data = read_kegg_orthology()
#         for kegg_id, kegg_data in kegg_data.items():
#             self.save_kegg_entry(kegg_id, kegg_data)
#
#     def save_kegg_entry(self, kegg_id, data):
#         name, parent_id = data
#         try:
#             entry = models.KeggEntry(brite_id=kegg_id,
#                                      brite_name=name,
#                                      parent=kegg_cache.get(parent_id))
#             entry.save(using=self.database)
#         except IntegrityError:
#             entry = models.KeggEntry.objects\
#                 .using(self.database)\
#                 .get(brite_id=kegg_id)
#
#         kegg_cache[kegg_id] = entry
#
#
# GENOME_STATS_HEADERS = ['accession', 'length', 'num_contigs', 'n_50',
#                         'gc_content', 'type', 'completeness',
#                         'contamination', 'rna_5s', 'rna_16s', 'rna_23s',
#                         'trnas', 'num_genomes', 'num_proteins',
#                         'pangenome_size', 'core_prop', 'accessory_prop',
#                         'eggnog_prop', 'ipr_prop']
#
#
# def load_genome_stats(fs):
#     with open(fs) as f:
#         l = f.read().strip().split('\t')
#     return dict(zip(GENOME_STATS_HEADERS, l))
#
#
# COG_HEADERS = ['accession', 'name', 'count']
#
#
# def load_cog_stats(fs):
#     with open(fs) as f:
#         lines = [l.strip().split('\t') for l in f.readlines()]
#     cog_counts = [dict(zip(COG_HEADERS, l)) for l in lines]
#     return cog_counts
#
#
# IPR_HEADERS = ['accession', 'rank', 'ipr_accession', 'count']
#
#
# def load_ipr_stats(fs):
#     with open(fs) as f:
#         lines = [l.strip().split('\t') for l in f.readlines()]
#     ipr_matches = [dict(zip(IPR_HEADERS, l)) for l in lines]
#     return ipr_matches
#
#
# KEGG_HEADERS = ['accession', 'kegg_id', 'count']
#
#
# def load_kegg_stats(fs):
#     with open(fs) as f:
#         lines = [l.strip().split('\t') for l in f.readlines()]
#     kegg_matches = [dict(zip(KEGG_HEADERS, l)) for l in lines]
#     return kegg_matches
#
#
# def validate_genome_dir(d):
#     fs = set(os.listdir(d))
#     if len(EXPECTED_FILES.difference(fs)):
#         missing_files = ", ".join(EXPECTED_FILES.difference(fs))
#         raise ValueError(
#             'Files are missing from directory {}: {}'.format(d, missing_files))
#
#
# def read_kegg_orthology():
#     with open(KEGG_ORTHOLOGY) as f:
#         kegg = json.load(f)
#     entries = {}
#
#     def find_nodes(node, parent_id=None, depth=0):
#         match = re.findall('^([^K]\d+) ([^[]*)', node['name'])
#         if len(match) > 0:
#             node_id, node_name = match[0]
#             if node_id not in entries:
#                 entries[node_id] = [node_name, parent_id]
#
#             children = node.get('children') or []
#             for child in children:
#                 find_nodes(child, parent_id=node_id, depth=depth + 1)
#
#     for child_node in kegg['children']:
#         find_nodes(child_node)
#     return entries
#
#
# def parse_args():
#     parser = argparse.ArgumentParser(
#         description='Tool to populate emg database with latest set of genomes')
#     parser.add_argument('-db', '--database', help='Target django database',
#                         default='default')
#     parser.add_argument('--reload-kegg',
#                         help='Download full kegg orthology '
#                              'and load BRITE to db',
#                         action='store_true')
#     parser.add_argument('-d', '--directory',
#                         help='Directory containing genome output', default='.')
#     return parser.parse_args()
#
#
# def main():
#     args = parse_args()
#     GenomePopulator(args)
#
#
# if __name__ == '__main__':
#     main()
