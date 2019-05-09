import os
import glob
import logging
import sys

logger = logging.getLogger(__name__)

EXPECTED_FILES = {'accessory_genome_cds.fa', 'cog_counts.tab',
                  'core_genome_cds.fa', 'eggnog_raw.tab', 'eggnog_top10.tab',
                  'genome_cds.fa', 'genome_seq.fa', 'genome_stats.tab',
                  'ipr_raw.tab', 'ipr_top10.tab', 'kegg_counts.tab',
                  'pan_genome_cds.fa'}


def sanity_check_result_dirs(dirs):
    errors = set()
    for d in dirs:
        try:
            fs = set(os.listdir(d))
            if len(EXPECTED_FILES.difference(fs)):
                missing_files = ", ".join(EXPECTED_FILES.difference(fs))
                raise ValueError(
                    'Files missing in directory {}: {}'.format(d,
                                                               missing_files))

            for f in fs:
                f_path = os.path.join(d, f)
                if not os.path.isfile(f_path):
                    raise ValueError(
                        '{} is a directory, file was expected.'.join(f_path))

                if os.stat(f_path).st_size == 0:
                    raise ValueError('{} is empty'.format(f_path))
        except ValueError as e:
            errors.add(e)
    if errors:
        for e in errors:
            logger.error(e)
        logger.error('Validation failed, see errors above')
        sys.exit(1)


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


def find_results(release_dir):
    return glob.glob(os.path.join(release_dir, '*'))


def get_result_path(genome_dir):
    sub_path = os.path.normpath(genome_dir).split(os.sep)[-2:]
    return os.path.join(*sub_path)
