import logging
import os
import json

DIR_NAME = os.path.dirname(__file__)

library_strategy_remapping = {
    'rna-seq': 'wgs',
    'wga': 'wgs'
}


def get_downloadset_config(version, library_strategy):
    _library_strategy = library_strategy.lower()
    logging.info("Loading config file for {}".format(_library_strategy))
    version_dir_name = 'v' + str(version).replace('.', '_')
    if _library_strategy in library_strategy_remapping:
        _library_strategy = library_strategy_remapping[_library_strategy]
    config_file = os.path.join(DIR_NAME, version_dir_name, _library_strategy + '.json')
    result = read_config(config_file)
    logging.info("Config file {} successfully loaded!".format(config_file))
    return result


def read_config(config_file):
    with open(config_file) as f:
        return json.load(f)['files']
