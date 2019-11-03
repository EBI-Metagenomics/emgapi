import glob
import os
import sys
from subprocess import check_output

from emgapianns.management.lib.utils import read_chunkfile
from emgapianns.management.webuploader_configs import get_downloadset_config


class SanityCheck:
    QC_NOT_PASSED = 'no-seqs-passed-qc-flag'
    EXPECTED_EXPERIMENT_TYPES = ['amplicon', 'wgs', 'assembly', 'rna-seq', 'other']

    # TODO: Introduce coverage check:
    # For Amplicnn datasets one of the following must exist: UNITE, ITSonedb, SSU or LSU annotations
    # For WGS and assembly datasets proteins must be predicted and they must have some annotations (e.g. InterProScan 5)
    def __init__(self, accession, d, experiment_type, version):
        self.dir = d
        self.prefix = os.path.basename(d)
        self.accession = accession
        self.experiment_type = experiment_type.lower()
        if self.experiment_type not in self.EXPECTED_EXPERIMENT_TYPES:
            sys.exit('Unexpected experiment type specified: {}'.format(self.experiment_type))
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

    def coverage_check(self):
        """
            For WGS / metaT, I’d do ’do proteins exist? If not, quit with error.
            If so, check for functional annotations.
            If functional annotations, proceed with upload.
            if no functional annotations - throw a warning / require manual intervention before upload.


            For Amplicon I do 'do LSU or SSU or ITS exist' If not quit with error
        :return:
        """
        if self.experiment_type == 'amplicon':
            files_to_check = []
            for f in self.config:
                if 'coverage_check' in f:
                    files_to_check.append(f)

            valid = False
            for check in files_to_check:
                try:
                    if check['_chunked']:
                        self.__check_chunked_file(check)
                    else:
                        self.__check_file(check)
                    valid = True
                    break
                except FileNotFoundError:
                    continue
            return valid
        else:
            # TODO: Implement
            pass

    def __count_number_of_lines(self, filepath):
        """
            Counts number of lines in text file.
        :return:
        """
        count = check_output("wc -l < {}".format(filepath), shell=True).rstrip()
        return int(count)

    def __count_number_of_seqs(self,filepath):
        """
            Counts number of sequences in compressed fastq file.
        :return:
        """
        count = check_output("zcat {} | wc -l".format(filepath), shell=True).rstrip()
        return int(count) / 4

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
