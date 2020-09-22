#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2020 EMBL - European Bioinformatics Institute
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from unittest.mock import patch
import pytest

from emgapianns.management.lib import sanity_check  # noqa: E402
from emgapianns.management.lib.uploader_exceptions import (NoAnnotationsFoundException,
                                                           UnexpectedLibraryStrategyException, QCNotPassedException,
                                                           CoverageCheckException)


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

    @patch("os.path.basename")
    @pytest.mark.parametrize("expected_accession, experiment_type, version, expected_result_dir", [
        ("ERRXXXXXX", "amplicon", "4.1", "/tmp"),
        ("ERRXXXXXX", "amplicon", "5.0", "/tmp"),
        ("ERZXXXXXX", "assembly", "4.1", "/tmp"),
        ("ERZXXXXXX", "assembly", "5.0", "/tmp"),
        ("ERRXXXXXX", "wgs", "4.1", "/tmp"),
        ("ERRXXXXXX", "wgs", "5.0", "/tmp"),
        ("ERRXXXXXX", "rna-seq", "4.1", "/tmp"),
        ("ERRXXXXXX", "rna-seq", "5.0", "/tmp"),
        ("ERRXXXXXX", "wga", "4.1", "/tmp"),
        ("ERRXXXXXX", "wga", "5.0", "/tmp"),
        ("ERZXXXXXX", "ASSEMBLY", "4.1", "/tmp"),
        ("ERRXXXXXX", "WGS", "4.1", "/tmp"),
        ("ERRXXXXXX", "AMPLICON", "4.1", "/tmp")
    ])
    def test_check_initialisations(self, mock_dir, expected_accession, experiment_type, version,
                                   expected_result_dir):
        mock_dir.return_value = "test"
        test_instance = sanity_check.SanityCheck(expected_accession, expected_result_dir, experiment_type, version)
        self.run_init_tests(test_instance, expected_accession, expected_result_dir, mock_dir.return_value)

    @patch("os.path.basename")
    @pytest.mark.parametrize("accession, experiment_type, version, result_folder", [
        ("ERR2985769", "wgs", "1.0", "/tmp"),
        ("ERR2985769", "wgs", "2.0", "/tmp"),
        ("ERR2985769", "wgs", "3.0", "/tmp"),
        ("ERR2985769", "rna-seq", "1.0", "/tmp"),
        ("ERR2985769", "rna-seq", "2.0", "/tmp"),
        ("ERR2985769", "rna-seq", "3.0", "/tmp"),
        ("ERR2985769", "amplicon", "1.0", "/tmp"),
        ("ERR2985769", "amplicon", "2.0", "/tmp"),
        ("ERR2985769", "amplicon", "3.0", "/tmp"),
        ("ERR2985769", "assembly", "1.0", "/tmp"),
        ("ERR2985769", "assembly", "2.0", "/tmp"),
        ("ERR2985769", "assembly", "3.0", "/tmp")
    ])
    def test_check_initialisation_should_raise_exception(self, mock_dir, accession, experiment_type, version,
                                                         result_folder):
        mock_dir.return_value = "test"
        with pytest.raises(FileNotFoundError):
            sanity_check.SanityCheck(accession, result_folder, experiment_type, version)

    @patch("os.path.basename")
    @pytest.mark.parametrize("accession, experiment_type, version, result_folder", [
        ("ERR2985769", "other", "4.1", "/tmp"),
        ("ERR2985769", "WXS", "4.1", "/tmp"),
    ])
    def test_check_init_should_raise_unexpected_library_strategy_exception(self, mock_dir, accession,
                                                                           experiment_type, version,
                                                                           result_folder):
        mock_dir.return_value = "test"
        with pytest.raises(UnexpectedLibraryStrategyException):
            sanity_check.SanityCheck(accession, result_folder, experiment_type, version)

    @pytest.mark.parametrize("accession, experiment_type, amplicon_type, version, result_folder", [
        ("ERR3506537", "amplicon", "SSU", "4.1",
         "results/2019/09/ERP117125/version_4.1/ERR350/007/ERR3506537_MERGED_FASTQ"),
        ("ERR2237853", "amplicon", "ITS", "5.0",
         "results/2018/01/ERP106131/version_5.0/ERR223/003/ERR2237853_MERGED_FASTQ")
    ])
    def test_check_amplicons_v4_v5_results_succeeds(self, accession, experiment_type, amplicon_type, version,
                                                    result_folder):
        root_dir = os.path.join(os.path.dirname(__file__), "test_data")
        result_dir = os.path.join(root_dir, result_folder)
        test_instance = sanity_check.SanityCheck(accession, result_dir, experiment_type, version)
        test_instance.check_file_existence()

    def test_check_amplicon_ssu_v5_results_succeeds(self):
        accession = "ERR2237853"
        experiment_type = "amplicon"
        version = "5.0"
        root_dir = os.path.join(os.path.dirname(__file__), "test_data")
        result_dir = os.path.join(root_dir,
                                  "results/2018/01/ERP106131/version_{}/ERR223/003/{}_MERGED_FASTQ".format(version,
                                                                                                           accession))
        test_instance = sanity_check.SanityCheck(accession, result_dir, experiment_type, version)
        test_instance.check_file_existence()

    @pytest.mark.parametrize("accession, experiment_type, version, result_folder", [
        ("ERR2985769", "amplicon", "4.1", "no-results")
    ])
    def test_check_amplicon_v4_results_raise_exception(self, accession, experiment_type, version, result_folder):
        root_dir = os.path.join(os.path.dirname(__file__), "test_data")
        result_dir = os.path.join(root_dir, result_folder)
        test_instance = sanity_check.SanityCheck(accession, result_dir, experiment_type, version)
        with pytest.raises(FileNotFoundError):
            test_instance.check_file_existence()

    @pytest.mark.parametrize("accession, experiment_type, version, result_folder", [
        ("ERZ477576", "assembly", "4.1",
         "results/2017/11/ERP104174/version_4.1/ERZ477/006/ERZ477576_FASTA"),
        ("ERZ782882", "assembly", "5.0",
         "sanity_check/version_5.0/assembly/ERZ782882_FASTA"),
        ("ERZ782883", "assembly", "5.0",
         "sanity_check/version_5.0/assembly/ERZ782883_FASTA")
    ])
    def test_check_assemblies_v4_v5_results_succeeds(self, accession, experiment_type, version, result_folder):
        root_dir = os.path.join(os.path.dirname(__file__), "test_data")
        result_dir = os.path.join(root_dir, result_folder)
        test_instance = sanity_check.SanityCheck(accession, result_dir, experiment_type, version)
        test_instance.check_file_existence()

    @pytest.mark.parametrize("accession, experiment_type, version, result_folder", [
        ("ERR1913139", "wgs", "4.1", "sanity_check/version_4.1/wgs/ERR1913139_FASTQ"),
        ("ERR1697182", "wgs", "5.0", "sanity_check/version_5.0/wgs/ERR1697182_MERGED_FASTQ")
    ])
    def test_check_file_existence_wgs_v4_v5_results_succeeds(self, accession, experiment_type, version, result_folder):
        root_dir = os.path.join(os.path.dirname(__file__), "test_data")
        result_dir = os.path.join(root_dir, result_folder)
        test_instance = sanity_check.SanityCheck(accession, result_dir, experiment_type, version)
        test_instance.check_file_existence()

    @pytest.mark.parametrize("accession, experiment_type, version, result_folder", [
        ("ERR1864826", "amplicon", "4.1",
         "results/2019/02/ERP021864/version_4.1/ERR1864826_FASTQ")
    ])
    def test_check_qc_not_passed_raise_exception(self, accession, experiment_type, version, result_folder):
        root_dir = os.path.join(os.path.dirname(__file__), "test_data")
        result_dir = os.path.join(root_dir, result_folder)
        test_instance = sanity_check.SanityCheck(accession, result_dir, experiment_type, version)
        with pytest.raises(QCNotPassedException):
            test_instance.run_quality_control_check()

    @pytest.mark.parametrize("accession, experiment_type, version, result_folder", [
        ("ERR1913139", "wgs", "4.1",
         "sanity_check/version_4.1/wgs/ERR1913139_FASTQ")
    ])
    def test_check_qc_not_passed_do_not_raise_exception(self, accession, experiment_type, version, result_folder):
        root_dir = os.path.join(os.path.dirname(__file__), "test_data")
        result_dir = os.path.join(root_dir, result_folder)
        test_instance = sanity_check.SanityCheck(accession, result_dir, experiment_type, version)
        test_instance.run_quality_control_check()
        assert True

    @pytest.mark.parametrize("accession, experiment_type, version, result_folder", [
        ("ERR0000001", "amplicon", "4.1",
         "results/2019/02/ERP000001/version_4.1/ERR0000001_FASTQ"),
        ("ERR3506531", "amplicon", "4.1",
         "results/2019/09/ERP117125/version_4.1/ERR350/001/ERR3506531_MERGED_FASTQ"),
        ("ERR1697183", "wgs", "5.0", "sanity_check/version_5.0/wgs/ERR1697183_MERGED_FASTQ")
    ])
    def test_check_file_existence_should_raise_file_not_found_error(self, accession, experiment_type, version,
                                                                    result_folder):
        root_dir = os.path.join(os.path.dirname(__file__), "test_data")
        result_dir = os.path.join(root_dir, result_folder)
        test_instance = sanity_check.SanityCheck(accession, result_dir, experiment_type, version)
        with pytest.raises(FileNotFoundError):
            test_instance.check_file_existence()

    @pytest.mark.parametrize("accession, experiment_type, version, result_folder", [
        ("ERR3506537", "amplicon", "4.1",
         "results/2019/09/ERP117125/version_4.1/ERR350/007/ERR3506537_MERGED_FASTQ"),
        ("ERR2237853", "amplicon", "5.0",
         "results/2018/01/ERP106131/version_5.0/ERR223/003/ERR2237853_MERGED_FASTQ"),
        ("ERZ782882", "assembly", "5.0",
         "sanity_check/version_5.0/assembly/ERZ782882_FASTA"),
        ("ERR3506532", "wgs", "4.1",
         "results/2019/09/ERP117125/version_4.1/ERR350/002/ERR3506532_MERGED_FASTQ"),
        ("ERR1697182", "wgs", "5.0", "sanity_check/version_5.0/wgs/ERR1697182_MERGED_FASTQ")
    ])
    def test_coverage_check_succeeds(self, accession, experiment_type, version, result_folder):
        root_dir = os.path.join(os.path.dirname(__file__), "test_data")
        result_dir = os.path.join(root_dir, result_folder)
        test_instance = sanity_check.SanityCheck(accession, result_dir, experiment_type, version)
        test_instance.run_coverage_check()
        assert True

    @pytest.mark.parametrize("accession, experiment_type, version, result_folder", [
        ("ERR3506531", "amplicon", "4.1",
         "results/2019/09/ERP117125/version_4.1/ERR350/001/ERR3506531_MERGED_FASTQ"),
        ("ERR1913139", "wgs", "4.1",
         "sanity_check/version_4.1/wgs/ERR1913139_FASTQ"),
        ("ERZ782883", "assembly", "5.0",
         "sanity_check/version_5.0/assembly/ERZ782883_FASTA"),
        ("ERR1864826", "amplicon", "4.1",
         "results/2019/02/ERP021864/version_4.1/ERR1864826_FASTQ"),
        ("ERR1697183", "wgs", "5.0", "sanity_check/version_5.0/wgs/ERR1697183_MERGED_FASTQ")
    ])
    def test_coverage_check_should_raise_coverage_check_exception(self, accession, experiment_type, version,
                                                                    result_folder):
        root_dir = os.path.join(os.path.dirname(__file__), "test_data")
        result_dir = os.path.join(root_dir, result_folder)
        test_instance = sanity_check.SanityCheck(accession, result_dir, experiment_type, version)
        with pytest.raises(CoverageCheckException):
            test_instance.run_coverage_check()
