import logging
import os
import json

DIR_NAME = os.path.dirname(__file__)

library_strategy_remapping = {
    'rna-seq': 'wgs',
    'wga': 'wgs'
}

#No config for no-tax. Just skip the coverage check in sanity check.
config_statuses = ['no_cds', 'no_qc']


def get_downloadset_config(version, library_strategy, result_status=None):
    _library_strategy = library_strategy.lower()
    version_dir_name = 'v' + str(version).replace('.', '_')
    if _library_strategy in library_strategy_remapping:
        _library_strategy = library_strategy_remapping[_library_strategy]
    if result_status in config_statuses:
        config_file = os.path.join(DIR_NAME, version_dir_name, result_status + '.json')
    else:
        config_file = os.path.join(DIR_NAME, version_dir_name, _library_strategy + '.json')
    logging.info("Loading config file {}".format(config_file))
    result = read_config(config_file)
    logging.info("Config file {} successfully loaded!".format(config_file))
    return result


def read_config(config_file):
    with open(config_file) as f:
        return json.load(f)['files']

