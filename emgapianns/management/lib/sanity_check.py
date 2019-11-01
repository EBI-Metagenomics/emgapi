import glob
import os

from emgapianns.management.lib.utils import read_chunkfile
from emgapianns.management.webuploader_configs import get_downloadset_config


class SanityCheck:
    QC_NOT_PASSED = 'no-seqs-passed-qc-flag'

    # TODO: Introduce coverage check:
    # For Amplicnn datasets one of the following must exist: UNITE, ITSonedb, SSU or LSU annotations
    # For WGS and assembly datasets proteins must be predicted and they must have some annotations (e.g. InterProScan 5)
    def __init__(self, accession, d, experiment_type, version):
        self.dir = d
        self.prefix = os.path.basename(d)
        self.accession = accession
        self.config = get_downloadset_config(version, experiment_type)

    def check_file_existence(self):
        for f in self.config:
            try:
                if f['_chunked']:
                    self.__check_chunked_file(f)
                else:
                    self.__check_file(f)
            except FileNotFoundError as e:
                if f['_required']:
                    raise e

    def check_for_qc_not_passed_flag(self):
        file_path = os.path.join(self.dir, self.QC_NOT_PASSED)
        try:
            self.__check_exists(file_path)
            return True
        except FileNotFoundError as e:
            return False

    def __check_chunked_file(self, file_config):
        chunk_file = file_config['chunk_file']
        if '{}' in chunk_file:
            chunk_file = chunk_file.format(self.prefix)
        chunk_filepath = self.get_filepath(file_config, chunk_file)
        chunks = read_chunkfile(chunk_filepath)
        for f in chunks:
            filepath = self.get_filepath(file_config, f)
            self.__check_exists(filepath)

    def get_filepath(self, file_config, filename):
        if file_config['subdir']:
            p = [self.dir, file_config['subdir'], filename]
        else:
            p = [self.dir, filename]
        return os.path.join(*p)

    def __check_file(self, file_config):
        file_name = file_config['real_name']
        if '{}' in file_name:
            file_name = file_name.format(self.prefix)
        filepath = self.get_filepath(file_config, file_name)
        self.__check_exists(filepath)

    @staticmethod
    def __check_exists(filepath):
        if not glob.glob(filepath):
            raise FileNotFoundError('{} is missing'.format(filepath))
