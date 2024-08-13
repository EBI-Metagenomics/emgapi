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

import pandas as pd
import pytest
from model_bakery import baker
from pandas.testing import assert_frame_equal

from emgapianns.management.lib import study_summary_generator  # noqa: E402


@pytest.fixture
def study_summary(tmp_path):
    baker.make("emgapi.Study",
               secondary_accession="ERP106131",
               result_directory="test")
    study_summary = study_summary_generator.StudySummaryGenerator("ERP106131",
                                                                  5, tmp_path, None)
    study_summary.summary_dir = os.path.join(os.path.dirname(__file__), "test_data")
    return study_summary

@pytest.fixture
def study_summary_v5_assembly(tmp_path):
    baker.make("emgapi.Study",
               secondary_accession="ERP104174",
               result_directory="test")
    study_summary = study_summary_generator.StudySummaryGenerator("ERP104174",
                                                                  5, tmp_path, None)
    study_summary.summary_dir = os.path.join(os.path.dirname(__file__), "test_data")
    return study_summary

@pytest.fixture
def study_summary_v4_assembly(tmp_path):
    baker.make("emgapi.Study",
               secondary_accession="ERP104174",
               result_directory="test")
    study_summary = study_summary_generator.StudySummaryGenerator("ERP104174",
                                                                  4.1, tmp_path, None)
    study_summary.summary_dir = os.path.join(os.path.dirname(__file__), "test_data")
    return study_summary

@pytest.mark.django_db
class TestStudySummaryGenerator:

    def _test_data_dir(self):
        return os.path.join(os.path.dirname(__file__), "test_data")

    def _fixtures_dir(self):
        return os.path.join(self._test_data_dir(), "fixtures")

    def compare_dataframes(self, study_df, file_name):
        test_file_name = os.path.join(self._fixtures_dir(), file_name)
        try:
            fixture = pd.read_csv(test_file_name, sep="\t", header=0, index_col=False)
            assert_frame_equal(fixture.reset_index(drop=True), study_df.reset_index(drop=True))
        except IOError:
            print("Cannot open file")

    @pytest.mark.parametrize("rna_type", [
        ("unite"),
        ("itsonedb"),
        ("LSU")
    ])
    def test_generate_taxonomy_phylum_summary_v5(self, study_summary, rna_type):
        analysis_result_dirs = dict()
        analysis_result_dirs["ERR2237853_MERGED_FASTQ"] = os.path.join(self._test_data_dir(),
                                                                       "ERR2237853_MERGED_FASTQ")
        analysis_result_dirs["ERR2237860_MERGED_FASTQ"] = os.path.join(self._test_data_dir(),
                                                                       "ERR2237860_MERGED_FASTQ")

        study_df = study_summary.generate_taxonomy_phylum_summary_v5(analysis_result_dirs, rna_type)
        self.compare_dataframes(study_df, "phylum_taxonomy_abundances_{}_v5.tsv".format(rna_type))

    def test_generate_ipr_summary_v5(self, study_summary_v5_assembly):
        """
            Tests InterProScan summary file generation on v5 assembly data.
        :param study_summary_v5_assembly: fixture
        :return:
        """
        analysis_result_dirs = dict()
        analysis_result_dirs["ERZ782882_FASTA"] = os.path.join(self._test_data_dir(),
                                                               "study_summary_generator/version_5.0/assembly/ERZ782882_FASTA")
        analysis_result_dirs["ERZ782883_FASTA"] = os.path.join(self._test_data_dir(),
                                                               "study_summary_generator/version_5.0/assembly/ERZ782883_FASTA")

        study_df = study_summary_v5_assembly.generate_ips_summary_v5(analysis_result_dirs)
        self.compare_dataframes(study_df, "IPR_abundances_v5.tsv")

    def test_generate_go_slim_summary_v5(self, study_summary_v5_assembly):
        """
            Tests GO slim summary file generation on v5 assembly data.
        :param study_summary_v5_assembly: fixture
        :return:
        """
        analysis_result_dirs = dict()
        analysis_result_dirs["ERZ782882_FASTA"] = os.path.join(self._test_data_dir(),
                                                               "study_summary_generator/version_5.0/assembly/ERZ782882_FASTA")
        analysis_result_dirs["ERZ782883_FASTA"] = os.path.join(self._test_data_dir(),
                                                               "study_summary_generator/version_5.0/assembly/ERZ782883_FASTA")

        study_df = study_summary_v5_assembly.generate_go_summary_v5(analysis_result_dirs, "slim")
        self.compare_dataframes(study_df, "GO-slim_abundances_v5.tsv")

    def test_generate_ipr_summary_v4(self, study_summary_v4_assembly):
        """
            Tests InterProScan summary file generation on v4 assembly data.
        :param study_summary_v4_assembly: fixture
        :return:
        """
        analysis_result_dirs = dict()
        analysis_result_dirs["ERZ782882_FASTA"] = os.path.join(self._test_data_dir(),
                                                               "study_summary_generator/version_4.1/assembly/ERZ782882_FASTA")
        analysis_result_dirs["ERZ782883_FASTA"] = os.path.join(self._test_data_dir(),
                                                               "study_summary_generator/version_4.1/assembly/ERZ782883_FASTA")

        study_df = study_summary_v4_assembly.generate_ips_summary_v4(analysis_result_dirs)
        self.compare_dataframes(study_df, "IPR_abundances_v4.tsv")

    def test_generate_go_slim_summary_v4(self, study_summary_v4_assembly):
        """
            Tests GO slim summary file generation on v4 assembly data.
        :param study_summary_v4_assembly: fixture
        :return:
        """
        analysis_result_dirs = dict()
        analysis_result_dirs["ERZ782882_FASTA"] = os.path.join(self._test_data_dir(),
                                                               "study_summary_generator/version_4.1/assembly/ERZ782882_FASTA")
        analysis_result_dirs["ERZ782883_FASTA"] = os.path.join(self._test_data_dir(),
                                                               "study_summary_generator/version_4.1/assembly/ERZ782883_FASTA")

        study_df = study_summary_v4_assembly.generate_go_summary_v4(analysis_result_dirs, "slim")
        self.compare_dataframes(study_df, "GO-slim_abundances_v4.tsv")

    @pytest.mark.parametrize("given,expected", [
        ("sk__Eukaryota", "Eukaryota;Unassigned;Unassigned"),
        ("sk__Eukaryota;k__", "Eukaryota;Unassigned;Unassigned"),
        ("sk__Eukaryota;k__;p__", "Eukaryota;Unassigned;Unassigned"),
        ("sk__Eukaryota;k__;p__Apicomplexa", "Eukaryota;Unassigned;Apicomplexa"),
        ("sk__Eukaryota;k__Fungi", "Eukaryota;Fungi;Unassigned"),
        ("sk__Eukaryota;k__Fungi;p__", "Eukaryota;Fungi;Unassigned"),
    ])
    def test_normalize_taxa_hierarchy(self, study_summary, given, expected):
        actual = study_summary.normalize_taxa_hierarchy(given)
        assert expected == actual

    @pytest.mark.parametrize("rna_type,expected", [
        ("LSU", ["ERR2237860_MERGED_FASTQ_LSU.fasta.mseq.tsv", "ERR2237853_MERGED_FASTQ_LSU.fasta.mseq.tsv"]),
        ("unite", ["ERR2237860_MERGED_FASTQ_unite.fasta.mseq.tsv", "ERR2237853_MERGED_FASTQ_unite.fasta.mseq.tsv"]),
        ("itsonedb",
         ["ERR2237860_MERGED_FASTQ_itsonedb.fasta.mseq.tsv", "ERR2237853_MERGED_FASTQ_itsonedb.fasta.mseq.tsv"])
    ])
    def test_get_mapseq_result_files(self, study_summary, rna_type, expected):
        analysis_result_dirs = dict()
        analysis_result_dirs["ERR2237853_MERGED_FASTQ"] = os.path.join(self._test_data_dir(),
                                                                       "ERR2237853_MERGED_FASTQ")
        analysis_result_dirs["ERR2237860_MERGED_FASTQ"] = os.path.join(self._test_data_dir(),
                                                                       "ERR2237860_MERGED_FASTQ")
        actual = study_summary.get_mapseq_result_files(analysis_result_dirs, rna_type, ".fasta.mseq.tsv")
        assert 2 == len(actual)
        assert 2 == len(expected)
        for actual_item in actual:
            assert expected[0] in actual_item or expected[1] in actual_item

    @pytest.mark.parametrize("rna_type,expected", [
        ("SSU", "Taxonomic analysis SSU rRNA"),
        ("LSU", "Taxonomic analysis LSU rRNA"),
        ("unite", "Taxonomic analysis UNITE"),
        ("itsonedb", "Taxonomic analysis ITSoneDB")
    ])
    def test_get_group_type(self, study_summary, rna_type, expected):
        actual = study_summary._get_group_type(rna_type)
        assert expected == actual

    @pytest.mark.parametrize("rna_type,expected", [
        ("SSU", "Phylum level taxonomies SSU"),
        ("LSU", "Phylum level taxonomies LSU"),
        ("unite", "Phylum level taxonomies UNITE"),
        ("itsonedb", "Phylum level taxonomies ITSoneDB")
    ])
    def test_get_phylum_file_description(self, study_summary, rna_type, expected):
        actual = study_summary._get_phylum_file_description(rna_type)
        assert expected == actual

    @pytest.mark.parametrize("rna_type,expected", [
        ("SSU", "Taxonomic assignments SSU"),
        ("LSU", "Taxonomic assignments LSU"),
        ("unite", "Taxonomic assignments UNITE"),
        ("itsonedb", "Taxonomic assignments ITSoneDB")
    ])
    def test_get_abundance_file_description(self, study_summary, rna_type, expected):
        actual = study_summary._get_abundance_file_description(rna_type)
        assert expected == actual
