import os
import glob
import logging
import sys
import json
import csv

logger = logging.getLogger(__name__)

EXPECTED_RELEASE_FILES = {'phylo_tree.json'}


def get_expected_genome_files(accession):
    return {
        'annotation_coverage.tsv',
        'cazy_summary.tsv',
        'cog_summary.tsv',
        'kegg_classes.tsv',
        'kegg_modules.tsv',
        accession + '.faa',
        accession + '.fna',
        accession + '.gff',
        accession + '.stats',
        accession + '_eggNOG.tsv',
        accession + '_InterProScan.tsv'
    }


EXPECTED_PANGENOME_FILES = {
    'accessory_genes.faa',
    'annotation_coverage.tsv',
    'cazy_summary.tsv',
    'cog_summary.tsv',
    'core_genes.faa',
    'genes_presence-absence.tsv',
    'kegg_classes.tsv',
    'kegg_modules.tsv',
    'pan-genome.faa',
    'pan-genome_eggNOG.tsv',
    'pan-genome_InterProScan.tsv'
}
EXPECTED_DIR_CONTENT = {'genome.json', 'genome'}


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


REQUIRED_JSON_FIELDS = {
    'accession',
    'completeness',
    'contamination',
    'eggnog_coverage',
    'gc_content',
    'genome_set',
    'geographic_origin',
    'gold_biome',
    'ipr_coverage',
    'length',
    'n_50',
    'nc_rnas',
    'num_contigs',
    'num_proteins',
    'rna_16s',
    'rna_23s',
    'rna_5s',
    'taxon_lineage',
    'trnas',
    'type'
}

REQUIRED_JSON_PANGENOME_FIELDS = {
    'pangenome_accessory_size',
    'num_genomes_non_redundant',
    'geographic_range',
    'pangenome_core_size',
    'pangenome_eggnog_coverage',
    'num_genomes_total',
    'pangenome_ipr_coverage',
    'pangenome_size'
}


def sanity_check_genome_json(data):
    keys = data.keys()
    missing_req_keys = set(REQUIRED_JSON_FIELDS).difference(set(keys))
    if len(missing_req_keys):
        raise ValueError('{} JSON is missing fields: '.format(
            data.get('accession'), " ".join(missing_req_keys)))

    if 'pangenome_stats' in data:
        p_data = data['pangenome_stats']
        p_keys = set(p_data.keys())
        missing_preq_keys = set(REQUIRED_JSON_PANGENOME_FIELDS).difference(
            set(p_keys))
        if len(missing_preq_keys):
            raise ValueError('{} JSON is missing fields: '.format(
                data['accession'], " ".join(missing_preq_keys)))


def sanity_check_genome_dir(accession, d):
    expected_files = get_expected_genome_files(accession)
    fs = os.listdir(d)
    missing = expected_files.difference(fs)
    if len(missing):
        missing_files = ", ".join(missing)
        raise ValueError(
            'Files missing in directory {}: {}'.format(d,
                                                       missing_files))


def sanity_check_pangenome_dir(d):
    fs = os.listdir(d)
    missing = EXPECTED_PANGENOME_FILES.difference(fs)
    if len(missing):
        missing_files = ", ".join(missing)
        raise ValueError(
            'Files missing in directory {}: {}'.format(d,
                                                       missing_files))


def sanity_check_genome_output(d):
    fs = set(os.listdir(d))
    missing = EXPECTED_DIR_CONTENT.difference(fs)
    if len(missing):
        raise ValueError('Files are missing from {}: {}'
                         .format(d, " ".join(missing)))

    json_file = os.path.join(d, 'genome.json')
    json_data = read_json(json_file)
    sanity_check_genome_json(json_data)

    genome_dir = os.path.join(d, 'genome')
    sanity_check_genome_dir(json_data['accession'], genome_dir)

    if 'pangenome' in json_data:
        pangenome_dir = os.path.join(d, 'pan-genome')
        sanity_check_pangenome_dir(pangenome_dir)


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
    return read_sep_f(fs, ',')


def read_tsv_w_headers(fs):
    return read_sep_f(fs, '\t')


def read_sep_f(fs, sep=None):
    with open(fs) as f:
        reader = csv.reader(f, skipinitialspace=True, delimiter=sep)
        header = next(reader)
        data = [dict(zip(header, row)) for row in reader]
        return data


def find_genome_results(release_dir):
    listdir = glob.glob(os.path.join(release_dir, '*'))
    return list(filter(os.path.isdir, listdir))


def find_release_files(release_dir):
    listdir = glob.glob(os.path.join(release_dir, '*'))
    return list(filter(os.path.isfile, listdir))


def get_result_path(genome_dir):
    sub_path = os.path.normpath(genome_dir).split(os.sep)[-2:]
    return os.path.join(*sub_path)
