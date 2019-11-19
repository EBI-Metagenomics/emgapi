import logging
import os
import json

DIR_NAME = os.path.dirname(__file__)

experiment_type_remapping = {
    'rna-seq': 'wgs',
    'other': 'wgs'
}


def get_downloadset_config(version, experiment_type):
    logging.info("Loading config file for {}".format(experiment_type))
    version_dir_name = 'v' + str(version).replace('.', '_')
    if experiment_type in experiment_type_remapping:
        experiment_type = experiment_type_remapping[experiment_type]
    config_file = os.path.join(DIR_NAME, version_dir_name, experiment_type.lower() + '.json')
    result = read_config(config_file)
    logging.info("Config file {} successfully loaded!")
    return result


def read_config(config_file):
    with open(config_file) as f:
        return json.load(f)['files']
