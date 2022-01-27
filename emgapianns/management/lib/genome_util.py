import os
import glob
import logging
import sys
import json
import csv

logger = logging.getLogger(__name__)

EXPECTED_CATALOGUE_FILES = {'phylo_tree.json'}


def get_expected_genome_files(accession):
    prefix = (accession + '_')
    return {
        prefix + 'annotation_coverage.tsv',
        prefix + 'cazy_summary.tsv',
        prefix + 'cog_summary.tsv',
        prefix + 'kegg_classes.tsv',
        prefix + 'kegg_modules.tsv',
        accession + '.faa',
        accession + '.fna',
        accession + '.gff',
        prefix + 'eggNOG.tsv',
        prefix + 'InterProScan.tsv'
    }


EXPECTED_PANGENOME_FILES = {
    'genes_presence-absence.Rtab',
    'pan-genome.fna',
}


def sanity_check_catalogue_dir(d):
    errors = set()
    files = find_catalogue_files(d)
    for f in files:
        try:
            logging.info('Loading file {}'.format(f))
            f = os.path.basename(f)
            EXPECTED_CATALOGUE_FILES.remove(f)
        except KeyError:
            logging.warning(
                'Unexpected file {} found in catalogue dir'.format(f))

    for f in EXPECTED_CATALOGUE_FILES:
        errors.add('Catalogue file {} is missing from dir'.format(f))

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
    'pangenome_core_size',
    'num_genomes_total',
    'pangenome_size'
}


def sanity_check_genome_json(data):
    keys = data.keys()
    missing_req_keys = set(REQUIRED_JSON_FIELDS).difference(set(keys))
    if len(missing_req_keys):
        raise ValueError('{} JSON is missing fields: {}'.format(
            data.get('accession'), " ".join(missing_req_keys)))

    if 'pangenome_stats' in data:
        p_data = data['pangenome_stats']
        p_keys = set(p_data.keys())
        missing_preq_keys = set(REQUIRED_JSON_PANGENOME_FIELDS).difference(
            set(p_keys))
        if len(missing_preq_keys):
            raise ValueError('{} JSON is missing fields: {}'.format(
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


def apparent_accession_of_genome_dir(d):
    """
    Gets the apparent accession of a genome directory, based on the folder name
    :param d: genome directory
    :return: e.g. MGYG0000000001
    """
    return os.path.basename(os.path.normpath(d))


def sanity_check_genome_output(d):
    apparent_accession = apparent_accession_of_genome_dir(d)
    if not os.path.isdir(os.path.join(d, 'genome')):
        raise ValueError(f'genome/ directory missing from {d}')
    if not os.path.exists(os.path.join(d, f'{apparent_accession}.json')):
        raise ValueError(f'{apparent_accession}.json missing from {d}')
    json_file = os.path.join(d, f'{apparent_accession}.json')
    json_data = read_json(json_file)
    sanity_check_genome_json(json_data)

    genome_dir = os.path.join(d, 'genome')
    sanity_check_genome_dir(json_data['accession'], genome_dir)


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


def find_genome_results(catalogue_dir):
    listdir = glob.glob(os.path.join(catalogue_dir, '*'))
    return list(filter(os.path.isdir, listdir))


def find_catalogue_files(catalogue_dir):
    listdir = glob.glob(os.path.join(catalogue_dir, '*'))
    return list(filter(os.path.isfile, listdir))


def get_genome_result_path(result_dir):
    return os.path.join('genomes', result_dir.split('genomes/')[-1])
