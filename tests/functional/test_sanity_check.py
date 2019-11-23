import os
from unittest.mock import patch
import pytest

from emgapianns.management.lib import sanity_check  # noqa: E402
from emgapianns.management.lib.uploader_exceptions import NoAnnotationsFoundException, UnexpectedLibraryStrategyException


class TestSanityCheck:

    @staticmethod
    def run_init_tests(actual, expected_accession, expected_result_dir, expected_prefix):
        assert expected_accession == actual.accession
        assert expected_result_dir == actual.dir
        assert expected_prefix == actual.prefix
        config = actual.config
        assert config is not None
        assert isinstance(config, list)
        assert len(config) > 0
        file = config[0]
        assert isinstance(file, dict)
        assert len(file) > 0
        assert "_required" in file
        assert "blah" not in file

    @patch('os.path.basename')
    @pytest.mark.parametrize("expected_accession, experiment_type, version, expected_result_dir", [
        ('ERRXXXXXX', 'amplicon', '4.1', '/tmp'),
        ('ERRXXXXXX', 'amplicon', '5.0', '/tmp'),
        ('ERZXXXXXX', 'assembly', '5.0', '/tmp'),
        ('ERZXXXXXX', 'assembly', '4.1', '/tmp'),
        ('ERRXXXXXX', 'wgs', '4.1', '/tmp'),
        ('ERRXXXXXX', 'rna-seq', '4.1', '/tmp'),
        ('ERZXXXXXX', 'ASSEMBLY', '4.1', '/tmp'),
        ('ERRXXXXXX', 'WGS', '4.1', '/tmp'),
        ('ERRXXXXXX', 'AMPLICON', '4.1', '/tmp')
    ])
    def test_check_initialisations(self, mock_dir, expected_accession, experiment_type, version,
                                   expected_result_dir):
        mock_dir.return_value = "test"
        test_instance = sanity_check.SanityCheck(expected_accession, expected_result_dir, experiment_type, version)
        self.run_init_tests(test_instance, expected_accession, expected_result_dir, mock_dir.return_value)

    @patch('os.path.basename')
    @pytest.mark.parametrize("accession, experiment_type, version, result_folder", [
        ('ERR2985769', 'wgs', '1.0', 'no-results'),
        ('ERR2985769', 'wgs', '5.0', '/tmp')
    ])
    def test_check_initialisation_should_raise_exception(self, mock_dir, accession, experiment_type, version,
                                                         result_folder):
        mock_dir.return_value = "test"
        with pytest.raises(FileNotFoundError):
            test_instance = sanity_check.SanityCheck(accession, result_folder, experiment_type, version)

    @patch('os.path.basename')
    @pytest.mark.parametrize("accession, experiment_type, version, result_folder", [
        ('ERR2985769', 'other', '4.1', '/tmp'),
    ])
    def test_check_init_should_raise_unexpected_ibrary_strategy_exception(self, mock_dir, accession, experiment_type, version,
                                                         result_folder):
        mock_dir.return_value = "test"
        with pytest.raises(UnexpectedLibraryStrategyException):
            test_instance = sanity_check.SanityCheck(accession, result_folder, experiment_type, version)

    @pytest.mark.parametrize("accession, experiment_type, amplicon_type, version, result_folder", [
        ('ERR3506537', 'amplicon', 'SSU', '4.1',
         'results/2019/09/ERP117125/version_4.1/ERR350/007/ERR3506537_MERGED_FASTQ'),
        ('ERR2237853', 'amplicon', 'ITS', '5.0',
         'results/2018/01/ERP106131/version_5.0/ERR223/003/ERR2237853_MERGED_FASTQ')
    ])
    def test_check_amplicons_v4_v5_results_succeeds(self, accession, experiment_type, amplicon_type, version,
                                                    result_folder):
        root_dir = os.path.dirname(__file__).replace('functional', 'test-input')
        result_dir = os.path.join(root_dir, result_folder)
        test_instance = sanity_check.SanityCheck(accession, result_dir, experiment_type, version)
        test_instance.check_file_existence()

    @pytest.mark.skip(reason="No example does exist yet")
    def test_check_amplicon_ssu_v5_results_succeeds(self):
        accession = 'ERR3506537'
        experiment_type = 'amplicon'
        version = '5.0'
        root_dir = os.path.dirname(__file__).replace('functional', 'test-input')
        result_dir = os.path.join(root_dir,
                                  'results/2019/09/ERP117125/version_{}/ERR350/007/{}_MERGED_FASTQ'.format(version,
                                                                                                           accession))
        test_instance = sanity_check.SanityCheck(accession, result_dir, experiment_type, version)
        test_instance.check_file_existence()

    @pytest.mark.parametrize("accession, experiment_type, version, result_folder", [
        ('ERR2985769', 'amplicon', '4.1', 'no-results')
    ])
    def test_check_amplicon_v4_results_raise_exception(self, accession, experiment_type, version, result_folder):
        root_dir = os.path.dirname(__file__).replace('functional', 'test-input')
        result_dir = os.path.join(root_dir, result_folder)
        test_instance = sanity_check.SanityCheck(accession, result_dir, experiment_type, version)
        with pytest.raises(FileNotFoundError):
            test_instance.check_file_existence()

    @pytest.mark.parametrize("accession, experiment_type, version, result_folder", [
        ('ERZ477576', 'assembly', '4.1',
         'results/2017/11/ERP104174/version_4.1/ERZ477/006/ERZ477576_FASTA'),
        ('ERZ477576', 'assembly', '5.0',
         'results/2017/11/ERP104174/version_5.0/ERZ477/006/ERZ477576_FASTA')
    ])
    def test_check_assemblies_v4_v5_results_succeeds(self, accession, experiment_type, version, result_folder):
        root_dir = os.path.dirname(__file__).replace('functional', 'test-input')
        result_dir = os.path.join(root_dir, result_folder)
        test_instance = sanity_check.SanityCheck(accession, result_dir, experiment_type, version)
        test_instance.check_file_existence()

    @pytest.mark.parametrize("accession, experiment_type, version, result_folder", [
        ('ERR1913139', 'wgs', '4.1',
         'results/2018/12/ERP019674/version_4.1/ERR1913139_FASTQ')
    ])
    def test_check_wgs_v4_v5_results_succeeds(self, accession, experiment_type, version, result_folder):
        root_dir = os.path.dirname(__file__).replace('functional', 'test-input')
        result_dir = os.path.join(root_dir, result_folder)
        test_instance = sanity_check.SanityCheck(accession, result_dir, experiment_type, version)
        test_instance.check_file_existence()

    @pytest.mark.skip(reason="No example does exist yet")
    def test_check_wgs_v5_results_succeeds(self):
        accession = '???'
        experiment_type = 'wgs'
        version = '5.0'
        root_dir = os.path.dirname(__file__).replace('functional', 'test-input')
        result_dir = os.path.join(root_dir,
                                  'results/2019/09/ERP117125/version_{}/ERR350/007/{}_MERGED_FASTQ'.format(version,
                                                                                                           accession))
        test_instance = sanity_check.SanityCheck(accession, result_dir, experiment_type, version)
        test_instance.check_file_existence()

    @pytest.mark.parametrize("accession, experiment_type, version, result_folder, expected_value", [
        ('ERR1864826', 'amplicon', '4.1',
         'results/2019/02/ERP021864/version_4.1/ERR1864826_FASTQ', False),
        ('ERR1913139', 'wgs', '4.1',
         'results/2018/12/ERP019674/version_4.1/ERR1913139_FASTQ', True)
    ])
    def test_check_qc_not_passed(self, accession, experiment_type, version, result_folder, expected_value):
        root_dir = os.path.dirname(__file__).replace('functional', 'test-input')
        result_dir = os.path.join(root_dir, result_folder)
        test_instance = sanity_check.SanityCheck(accession, result_dir, experiment_type, version)
        actual = test_instance.passed_quality_control()
        assert expected_value == actual

    @pytest.mark.parametrize("accession, experiment_type, version, result_folder", [
        ('ERR0000001', 'amplicon', '4.1',
         'results/2019/02/ERP000001/version_4.1/ERR0000001_FASTQ'),
        ('ERR3506531', 'amplicon', '4.1',
         'results/2019/09/ERP117125/version_4.1/ERR350/001/ERR3506531_MERGED_FASTQ')
    ])
    def test_check_file_existence_should_raise_file_not_found_error(self, accession, experiment_type, version,
                                                                    result_folder):
        root_dir = os.path.dirname(__file__).replace('functional', 'test-input')
        result_dir = os.path.join(root_dir, result_folder)
        test_instance = sanity_check.SanityCheck(accession, result_dir, experiment_type, version)
        with pytest.raises(FileNotFoundError):
            test_instance.check_file_existence()

    @pytest.mark.parametrize("accession, experiment_type, amplicon_type, version, result_folder, expected_value", [
        ('ERR3506537', 'amplicon', 'SSU', '4.1',
         'results/2019/09/ERP117125/version_4.1/ERR350/007/ERR3506537_MERGED_FASTQ', True),
        ('ERR2237853', 'amplicon', 'ITS', '5.0',
         'results/2018/01/ERP106131/version_5.0/ERR223/003/ERR2237853_MERGED_FASTQ', True),
        ('ERR1864826', 'amplicon', 'SSU', '4.1',
         'results/2019/02/ERP021864/version_4.1/ERR1864826_FASTQ', False),
        ('ERR3506532', 'wgs', 'WGS', '4.1',
         'results/2019/09/ERP117125/version_4.1/ERR350/002/ERR3506532_MERGED_FASTQ', True)
    ])
    def test_coverage_check_succeeds(self, accession, experiment_type, amplicon_type, version,
                                     result_folder, expected_value):
        root_dir = os.path.dirname(__file__).replace('functional', 'test-input')
        result_dir = os.path.join(root_dir, result_folder)
        test_instance = sanity_check.SanityCheck(accession, result_dir, experiment_type, version)
        actual = test_instance.passed_coverage_check()
        assert expected_value == actual

    @pytest.mark.parametrize("accession, experiment_type, version, result_folder", [
        ('ERR3506531', 'amplicon', '4.1',
         'results/2019/09/ERP117125/version_4.1/ERR350/001/ERR3506531_MERGED_FASTQ'),
        ('ERR1913139', 'wgs', '4.1',
         'results/2018/12/ERP019674/version_4.1/ERR1913139_FASTQ')
    ])
    def test_coverage_check_should_raise_no_annotations_found_error(self, accession, experiment_type, version,
                                                                    result_folder):
        root_dir = os.path.dirname(__file__).replace('functional', 'test-input')
        result_dir = os.path.join(root_dir, result_folder)
        test_instance = sanity_check.SanityCheck(accession, result_dir, experiment_type, version)
        with pytest.raises(NoAnnotationsFoundException):
            test_instance.passed_coverage_check()
