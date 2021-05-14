import logging
import os
import json

DIR_NAME = os.path.dirname(__file__)

library_strategy_remapping = {
    'rna-seq': 'wgs',
    'wga': 'wgs'
}


def get_downloadset_config(version, library_strategy, result_status=None):
    _library_strategy = library_strategy.lower()
    version_dir_name = 'v' + str(version).replace('.', '_')
    if _library_strategy in library_strategy_remapping:
        _library_strategy = library_strategy_remapping[_library_strategy]
    config_file = os.path.join(DIR_NAME, version_dir_name, _library_strategy + '.json')
    logging.info("Loading config file {}".format(config_file))
    result = filter_config(config_file, result_status)
    logging.info("Config file {} successfully loaded!".format(config_file))
    logging.info("Filtered config for result status {}".format(result_status))
    return result


def filter_config(config, result_status=None):
    """
    Remove absent files from config based on result status.
    All tax files are optional, so no filter required for no_qc.
    :param config: json config per library strategy
    :param result_status: no_cds, no_tax, no_qc, full or None for <= v4.1 analyses
    :return: original or filtered config
    """
    final_config = []
    no_qc_filter = ['Sequence data', 'Taxonomic analysis mOTU', 'Functional analysis', 'functional-annotation/stats',
                    'Taxonomic analysis LSU rRNA', 'Taxonomic analysis SSU rRNA', 'Taxonomic analysis UNITE',
                    'Taxonomic analysis ITSoneDB', 'krona.html', 'pathways-systems', 'functional-annotation',
                    'qc-statistics', '{}.cmsearch.all.tblout.gz', '{}.cmsearch.all.tblout.deoverlapped.gz',
                    'RNA-counts']
    no_cds_filter = ['functional-annotation/stats', 'Pathways and Systems', 'pathways-systems', 'Functional analysis',
                     'functional-annotation', '{}_CDS.faa.gz', '{}_CDS.ffn.gz']
    no_filter = ['full', 'no_tax']
    if not result_status or result_status in no_filter:
        return read_config(config)
    filter = eval(result_status + '_filter')
    for file in read_config(config):
        if 'antismash' in file['real_name'] or 'summary.out' in file['real_name']:
            final_config.append(file)
        elif file['group_type'] in filter or file['subdir'] in filter or file['real_name'] in filter:
            continue
        else:
            final_config.append(file)
    return final_config


def read_config(config_file):
    with open(config_file) as f:
        return json.load(f)['files']

