import os
import json

DIR_NAME = os.path.dirname(__file__)

experiment_type_remapping = {
    'RNA-Seq': 'WGS',
    'OTHER': 'WGS'
}


def get_downloadset_config(version, experiment_type):
    version_dir_name = 'v' + str(version).replace('.', '_')
    if experiment_type in experiment_type_remapping:
        experiment_type = experiment_type_remapping[experiment_type]
    config_file = os.path.join(DIR_NAME, version_dir_name, experiment_type.lower() + '.json')
    return read_config(config_file)


def read_config(config_file):
    with open(config_file) as f:
        return json.load(f)['files']
