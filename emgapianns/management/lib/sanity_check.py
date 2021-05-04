import glob
import os
from subprocess import check_output, CalledProcessError

import logging

from emgapianns.management.lib.uploader_exceptions import NoAnnotationsFoundException, \
    UnexpectedLibraryStrategyException, QCNotPassedException, CoverageCheckException
from emgapianns.management.lib import utils
from emgapianns.management.webuploader_configs import get_downloadset_config
from backlog import models as backlog_models

logger = logging.getLogger(__name__)


def get_result_status(accession):
    """
    no_qc: upload qc results only. No downloads
    no_cds: upload qc and taxonomy. Antismash tab optional if files present.
    no_tax: standard upload (tax files are optional)
    no_cds_tax: use no_qc config. Upload qc. Processed reads and other ncRNA downloadable

    :param accession:
    :return: result status
    """
    result_status = backlog_models.AnnotationJob.objects.using('backlog_dev').filter(
        runs__primary_accession=accession).values_list('result_status', flat=True)
    if len(result_status):
        if result_status[0] == 'no_cds_tax':
            return 'no_qc'
        return result_status[0]


class SanityCheck:
    QC_NOT_PASSED_V4 = 'no-seqs-passed-qc-flag'
    QC_NOT_PASSED_V5 = 'QC-FAILED'
    EXPECTED_LIBRARY_STRATEGIES = ['amplicon', 'wgs', 'assembly', 'rna-seq', 'wga']
    MIN_NUM_SEQS = 1
    MIN_NUM_LINES = 3
    failed_statuses = ['no_cds', 'no_tax', 'no_qc', 'no_cds_tax']

    def __init__(self, accession, d, library_strategy, version, result_status=None):
        self.dir = d
        self.prefix = os.path.basename(d)
        self.accession = accession
        self.library_strategy = library_strategy.lower()
        self.version = version
        if self.library_strategy not in self.EXPECTED_LIBRARY_STRATEGIES:
            raise UnexpectedLibraryStrategyException(
                'Unexpected library_strategy specified: {}'.format(self.library_strategy))
        if version != '5.0':
            self.result_status = None
        elif version == '5.0' and result_status:
            self.result_status = result_status
        else:
            self.result_status = get_result_status(self.accession)
        self.config = get_downloadset_config(version, library_strategy, self.result_status)

    def check_file_existence(self):
        skip_antismash_check = False
        if os.path.exists(os.path.join(self.dir, "pathways-systems", "no-antismash")):
            logging.info("Found no-antismash flag! Skipping check of antiSMASH result files.")
            skip_antismash_check = True

        for f in self.config:
            if 'antismash' in f and skip_antismash_check:
                continue
            try:
                if f['_chunked']:
                    self.__check_chunked_file(f)
                else:
                    self.__check_file(f)
            except FileNotFoundError as e:
                if f['_required']:
                    raise e

    def run_quality_control_check(self):
        if self.version == '5.0':
            file_path = os.path.join(self.dir, self.QC_NOT_PASSED_V5)
        elif self.version == '4.1':
            file_path = os.path.join(self.dir, self.QC_NOT_PASSED_V4)

        try:
            self.__check_exists(file_path)
            if self.version == '4.1':
                raise QCNotPassedException("{} did not pass QC step!".format(self.accession))
            elif self.version == '5.0':
                logging.warning("{} did not pass QC step!".format(self.accession))
        except FileNotFoundError:
            pass  # QC not passed file does not exist, so all fine

    def run_coverage_check(self):
        """
            For WGS / metaT, I’d do ’do proteins exist? If not, quit with error.
            If so, check for functional annotations.
            If functional annotations, proceed with upload.
            if no functional annotations - throw a warning / require manual intervention before upload.

            For Amplicon I do 'do LSU or SSU or ITS exist' If not quit with error
        :return:
        """
        #skip coverage check qc-failed
        if self.result_status == 'no_qc':
            logging.info('{} found. Skipping coverage check'.format(self.result_status))
            return

        # For amplicons the requirement is that only of the files need to exist
        elif self.library_strategy == "assembly":  # assembly
            return self.run_coverage_check_assembly()
        else: # wgs or rna-seq
            return self.run_coverage_check_wgs()

    @staticmethod
    def __count_number_of_lines(filepath, compressed_file=False):
        """
            Counts number of lines in text file.
        :return:
        """
        if compressed_file:
            logging.info("Counting number of lines for compressed file {}".format(filepath))
            count = check_output("zcat {} | wc -l".format(filepath), shell=True).rstrip()
        else:
            logging.info("Counting number of lines for uncompressed file {}".format(filepath))
            count = check_output("wc -l < {}".format(filepath), shell=True).rstrip()
        logging.info("Result: File contains {} lines.".format(count))
        return int(count)

    @staticmethod
    def __count_number_of_seqs(filepath):
        """
            Counts number of sequences in compressed fasta file.
        :return:
        """
        try:
            logging.info("Counting number of sequences for compressed file {}".format(filepath))
            count = check_output("zcat {} | grep -c '>'".format(filepath), shell=True).rstrip()
            logging.info("Result: File contains {} sequences.".format(count))
            return int(count)
        except CalledProcessError:
            return 0

    def __check_chunked_file(self, file_config, coverage_check=False):
        chunk_file = file_config['chunk_file']
        if '{}' in chunk_file:
            chunk_file = chunk_file.format(self.prefix)
        chunk_filepath = self.get_filepath(file_config, chunk_file)
        chunks = utils.read_chunkfile(chunk_filepath)
        #chunks = read_chunkfile(chunk_filepath)
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
        file_exists = self.__check_exists(filepath, file_config['_required'])
        if coverage_check and file_exists:
            self.__check_file_content(filepath)

    @staticmethod
    def __check_exists(filepath, required=True):
        found_file = glob.glob(filepath)
        if not found_file and required:
            raise FileNotFoundError('{} is missing'.format(filepath))
        elif found_file:
            return True
        elif not found_file:
            return False

    def __check_file_content(self, filepath):
        logging.info("Checking content of file {}".format(filepath))
        if "faa.gz" in filepath:
            count = self.__count_number_of_seqs(filepath)
            if count >= self.MIN_NUM_SEQS:
                return True
        if "I5.tsv.gz" in filepath:
            num_lines = self.__count_number_of_lines(filepath, compressed_file=True)
            if num_lines >= self.MIN_NUM_LINES:
                return True
        else:
            num_lines = self.__count_number_of_lines(filepath)
            if num_lines >= self.MIN_NUM_LINES:
                return True
        raise NoAnnotationsFoundException('No annotations found in result file:\n{}'.format(filepath))

    def run_coverage_check_amplicon(self):
        """
            For Amplicon I do 'do LSU or SSU or ITS exist' If not quit with error
        :return:
        """
        logging.info("Running coverage check for amplicon data.")
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
                except NoAnnotationsFoundException:
                    continue
        if not valid:
            raise CoverageCheckException("{} did not pass coverage check step!".format(self.accession))

    def run_coverage_check_assembly(self):
        """
            For Assemblies, we do 'check for taxonomy output folder' If not, quit with error.
            If so, check ’do proteins exist? check.
            If so, check for functional annotations.
            If functional annotations, proceed with upload.
            if no functional annotations - throw a warning / require manual intervention before upload.
        :return:
        """
        logging.info("Running coverage check for assembly data.")
        taxa_folder = os.path.join(self.dir, "taxonomy-summary")
        if not os.path.exists(taxa_folder) and self.result_status not in ['no_tax', 'no_cds_tax']:
            raise CoverageCheckException("Could not find the taxonomy output folder: {}!".format(taxa_folder))

        for f in self.config:
            if 'coverage_check' in f:
                try:
                    if f['_chunked']:
                        logging.info("Processing chunked file {}".format(f['description_label']))
                        self.__check_chunked_file(f, coverage_check=True)
                    else:
                        logging.info("Processing unchunked file {}".format(f['description_label']))
                        self.__check_file(f, coverage_check=True)
                except FileNotFoundError:
                    # Label as coverage check NOT passed
                    raise CoverageCheckException("Could not find file for: "
                                                 "{}".format(f['description_label']))
                except NoAnnotationsFoundException:
                    # Label as coverage check NOT passed
                    raise CoverageCheckException("Could not find any annotations in the output file for: "
                                    "{}".format(f['description_label']))

    def run_coverage_check_wgs(self):
        """
            For WGS / metaT, we do 'check for taxonomy output folder' If not, quit with error.
            If so, check ’do proteins exist? check.
            If so, check for functional annotations.
            If functional annotations, proceed with upload.
            if no functional annotations - throw a warning / require manual intervention before upload.
        :return:
        """
        logging.info("Running coverage check for wgs data.")
        taxa_folder = os.path.join(self.dir, "taxonomy-summary")
        if not os.path.exists(taxa_folder) and self.result_status not in ['no_tax', 'no_cds_tax']:
            raise CoverageCheckException("Could not find the taxonomy output folder: {}!".format(taxa_folder))
            
        for f in self.config:
            if 'coverage_check' in f:
                try:
                    if f['_chunked']:
                        self.__check_chunked_file(f, coverage_check=True)
                    else:
                        self.__check_file(f, coverage_check=True)
                except FileNotFoundError:
                    # Label as coverage check NOT passed
                    raise CoverageCheckException("{} did not pass coverage check step!".format(self.accession))

                except NoAnnotationsFoundException:
                    # Label as coverage check NOT passed
                    raise CoverageCheckException("{} did not pass coverage check step!".format(self.accession))
