import os

from emgapianns.management.lib.utils import read_chunkfile
from emgapianns.management.webuploader_configs import get_downloadset_config


class SanityCheck:
    def __init__(self, accession, d, experiment_type, version):
        self.dir = d
        self.prefix = os.path.basename(d)
        self.accession = accession
        self.config = get_downloadset_config(version, experiment_type)

    def check_all(self):
        for f in self.config:
            try:
                if f['_chunked']:
                    self.check_chunked_file(f)
                else:
                    self.check_file(f)
            except FileNotFoundError as e:
                if f['_required']:
                    raise e

    def check_chunked_file(self, file_config):
        chunk_file = file_config['chunk_file']
        if '{}' in chunk_file:
            chunk_file = chunk_file.format(self.prefix)
        chunk_filepath = self.get_filepath(file_config, chunk_file)
        chunks = read_chunkfile(chunk_filepath)
        for f in chunks:
            filepath = self.get_filepath(file_config, f)
            self.check_exists(filepath)

    def get_filepath(self, file_config, filename):
        if file_config['subdir']:
            p = [self.dir, file_config['subdir'], filename]
        else:
            p = [self.dir, filename]
        return os.path.join(*p)

    def check_file(self, file_config):
        file_name = file_config['real_name']
        if '{}' in file_name:
            file_name = file_name.format(self.prefix)
        filepath = self.get_filepath(file_config, file_name)
        self.check_exists(filepath)

    @staticmethod
    def check_exists(filepath):
        if not os.path.exists(filepath):
            raise FileNotFoundError('{} is missing'.format(filepath))