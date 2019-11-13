import glob
import os
import sys
from subprocess import check_output, CalledProcessError

from emgapianns.management.lib.uploader_exceptions import NoAnnotationsFoundError
from emgapianns.management.lib.utils import read_chunkfile
from emgapianns.management.webuploader_configs import get_downloadset_config


class SanityCheck:
    QC_NOT_PASSED = 'no-seqs-passed-qc-flag'
    EXPECTED_EXPERIMENT_TYPES = ['amplicon', 'wgs', 'assembly', 'rna-seq', 'other']
    MIN_NUM_SEQS = 1
    MIN_NUM_LINES = 3

    def __init__(self, accession, d, experiment_type, version):
        self.dir = d
        self.prefix = os.path.basename(d)
        self.accession = accession
        self.experiment_type = experiment_type.lower()
        self.version = version
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

    def passed_quality_control(self):
        file_path = os.path.join(self.dir, self.QC_NOT_PASSED)
        try:
            self.__check_exists(file_path)
            return False
        except FileNotFoundError as e:
            return True

    def passed_coverage_check(self):
        """
            For WGS / metaT, I’d do ’do proteins exist? If not, quit with error.
            If so, check for functional annotations.
            If functional annotations, proceed with upload.
            if no functional annotations - throw a warning / require manual intervention before upload.

            For Amplicon I do 'do LSU or SSU or ITS exist' If not quit with error
        :return:
        """
        valid = False
        for f in self.config:
            if 'coverage_check' in f:
                try:
                    if f['_chunked']:
                        self.__check_chunked_file(f, coverage_check=True)
                    else:
                        self.__check_file(f, coverage_check=True)
                    valid = True
                    break
                except FileNotFoundError:
                    continue
        return valid

    @staticmethod
    def __count_number_of_lines(filepath):
        """
            Counts number of lines in text file.
        :return:
        """
        count = check_output("wc -l < {}".format(filepath), shell=True).rstrip()
        return int(count)

    @staticmethod
    def __count_number_of_seqs(filepath):
        """
            Counts number of sequences in compressed fasta file.
        :return:
        """
        try:
            count = check_output("zcat {} | grep -c '>'".format(filepath), shell=True).rstrip()
            return int(count)
        except CalledProcessError:
            return 0

    def __check_chunked_file(self, file_config, coverage_check=False):
        chunk_file = file_config['chunk_file']
        if '{}' in chunk_file:
            chunk_file = chunk_file.format(self.prefix)
        chunk_filepath = self.get_filepath(file_config, chunk_file)
        chunks = read_chunkfile(chunk_filepath)
        for f in chunks:
            filepath = self.get_filepath(file_config, f)
            self.__check_exists(filepath)
            if coverage_check:
                self.__check_file_content(filepath)

    def get_filepath(self, file_config, filename):
        if file_config['subdir']:
            p = [self.dir, file_config['subdir'], filename]
        else:
            p = [self.dir, filename]
        return os.path.join(*p)

    def __check_file(self, file_config, coverage_check=False):
        file_name = file_config['real_name']
        if '{}' in file_name:
            file_name = file_name.format(self.prefix)
        filepath = self.get_filepath(file_config, file_name)
        self.__check_exists(filepath)
        if coverage_check:
            self.__check_file_content(filepath)

    @staticmethod
    def __check_exists(filepath):
        if not glob.glob(filepath):
            raise FileNotFoundError('{} is missing'.format(filepath))

    def __check_file_content(self, filepath):
        if "faa.gz" in filepath:
            count = self.__count_number_of_seqs(filepath)
            if count >= self.MIN_NUM_SEQS:
                return True
        else:
            num_lines = self.__count_number_of_lines(filepath)
            if num_lines >= self.MIN_NUM_LINES:
                return True
        raise NoAnnotationsFoundError('No annotations found in result file:\n{}'.format(filepath))
