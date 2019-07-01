import os
import glob
import logging
import sys
import json
import csv

logger = logging.getLogger(__name__)

EXPECTED_RELEASE_FILES = {'phylo_tree.json'}

EXPECTED_GENOME_FILES = {'accessory_genome_cds.fa', 'cog_counts.csv',
                         'core_genome_cds.fa', 'eggnog_raw.tab',
                         'eggnog_top10.csv',
                         'genome_cds.fa', 'genome_seq.fa', 'genome_stats.json',
                         'ipr_raw.tab', 'ipr_top10.csv', 'kegg_counts.csv',
                         'pan_genome_cds.fa'}


def sanity_check_release_dir(d):
    errors = set()
    files = find_release_files(d)
    for f in files:
        try:
            logging.info('Loading file {}'.format(f))

            f = os.path.basename(f)
            EXPECTED_RELEASE_FILES.remove(f)
        except KeyError:
            logging.warning(
                'Unexpected file {} found in release dir'.format(f))

    for f in EXPECTED_RELEASE_FILES:
        errors.add('Release file {} is missing from dir'.format(f))

    if errors:
        for e in errors:
            logger.error(e)
        logger.error('Validation failed, see errors above')
        sys.exit(1)


def sanity_check_genome_dirs(dirs):
    errors = set()
    for d in dirs:
        try:
            fs = set(os.listdir(d))
            if len(EXPECTED_GENOME_FILES.difference(fs)):
                missing_files = ", ".join(
                    EXPECTED_GENOME_FILES.difference(fs))
                raise ValueError(
                    'Files missing in directory {}: {}'.format(d,
                                                               missing_files))

            for f in fs:
                f_path = os.path.join(d, f)
                if not os.path.isfile(f_path):
                    raise ValueError(
                        '{} is a directory, file was expected.'.join(
                            f_path))

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


def read_json(fs):
    with open(fs) as f:
        return json.load(f)


def read_csv_w_headers(fs):
    with open(fs) as f:
        reader = csv.reader(f, skipinitialspace=True)
        header = next(reader)
        data = [dict(zip(header, row)) for row in reader]
        return data


def validate_genome_dir(d):
    fs = set(os.listdir(d))
    if len(EXPECTED_GENOME_FILES.difference(fs)):
        missing_files = ", ".join(EXPECTED_GENOME_FILES.difference(fs))
        raise ValueError(
            'Files are missing from directory {}: {}'.format(d, missing_files))


def find_genome_results(release_dir):
    listdir = glob.glob(os.path.join(release_dir, '*'))
    return list(filter(os.path.isdir, listdir))

def find_release_files(release_dir):
    listdir = glob.glob(os.path.join(release_dir, '*'))
    return list(filter(os.path.isfile, listdir))

def get_result_path(genome_dir):
    sub_path = os.path.normpath(genome_dir).split(os.sep)[-2:]
    return os.path.join(*sub_path)
