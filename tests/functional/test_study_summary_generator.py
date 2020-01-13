import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
from pandas.util.testing import assert_frame_equal
from parameterized import parameterized

from emgapianns.management.lib import study_summary_generator  # noqa: E402


class TestStudySummaryGenerator(unittest.TestCase):

    @patch('emgapianns.management.lib.study_summary_generator.emg_models')
    def setUp(self, mock_model):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        mock_model.Study.objects.using().get().result_directory = "test"
        self.test_instance = study_summary_generator.StudySummaryGenerator("ERP106131", 5, self.test_dir, None, None)

        """ Your setUp """
        script_path = os.path.dirname(__file__)
        test_input_dir = script_path.replace('functional', 'test-input')
        self.fixtures_dir = os.path.join(test_input_dir, 'fixtures')
        self.test_instance.summary_dir = test_input_dir

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)
        self.test_instance = None

    def compare_dataframes(self, study_df, file_name):
        test_file_name = os.path.join(self.fixtures_dir, file_name)
        try:
            fixture = pd.read_csv(test_file_name, sep='\t', header=0, index_col=False)
            assert_frame_equal(fixture.reset_index(drop=True), study_df.reset_index(drop=True))
        except IOError:
            print('Cannot open file')

    @parameterized.expand([
        ("unite"),
        ("itsonedb"),
        ("LSU")
    ])
    def test_generate_taxonomy_phylum_summary_v5(self, rna_type):

        analysis_result_dirs = dict()
        #
        rootpath = os.path.dirname(__file__).replace('functional', 'test-input')
        analysis_result_dirs['ERR2237853_MERGED_FASTQ'] = os.path.join(rootpath, "ERR2237853_MERGED_FASTQ")
        analysis_result_dirs['ERR2237860_MERGED_FASTQ'] = os.path.join(rootpath, "ERR2237860_MERGED_FASTQ")

        study_df = self.test_instance.generate_taxonomy_phylum_summary_v5(analysis_result_dirs, rna_type)
        self.compare_dataframes(study_df, 'phylum_taxonomy_abundances_{}_v5.tsv'.format(rna_type))

    @parameterized.expand([
        ("sk__Eukaryota", "Eukaryota;Unassigned;Unassigned"),
        ("sk__Eukaryota;k__", "Eukaryota;Unassigned;Unassigned"),
        ("sk__Eukaryota;k__;p__", "Eukaryota;Unassigned;Unassigned"),
        ("sk__Eukaryota;k__;p__Apicomplexa", "Eukaryota;Unassigned;Apicomplexa"),
        ("sk__Eukaryota;k__Fungi", "Eukaryota;Fungi;Unassigned"),
        ("sk__Eukaryota;k__Fungi;p__", "Eukaryota;Fungi;Unassigned"),
    ])
    def test_normalize_taxa_hierarchy(self, given, expected):
        actual = self.test_instance.normalize_taxa_hierarchy(given)
        assert expected == actual

    @parameterized.expand([
        ("LSU", ['ERR2237860_MERGED_FASTQ_LSU.fasta.mseq.tsv', 'ERR2237853_MERGED_FASTQ_LSU.fasta.mseq.tsv']),
        ("unite", ['ERR2237860_MERGED_FASTQ_unite.fasta.mseq.tsv', 'ERR2237853_MERGED_FASTQ_unite.fasta.mseq.tsv']),
        ("itsonedb", ['ERR2237860_MERGED_FASTQ_itsonedb.fasta.mseq.tsv', 'ERR2237853_MERGED_FASTQ_itsonedb.fasta.mseq.tsv'])
    ])
    def test_get_mapseq_result_files(self, rna_type, expected):

        analysis_result_dirs = dict()
        rootpath = os.path.dirname(__file__).replace('functional', 'test-input')
        analysis_result_dirs['ERR2237853_MERGED_FASTQ'] = os.path.join(rootpath, "ERR2237853_MERGED_FASTQ")
        analysis_result_dirs['ERR2237860_MERGED_FASTQ'] = os.path.join(rootpath, "ERR2237860_MERGED_FASTQ")
        #
        actual = self.test_instance.get_mapseq_result_files(analysis_result_dirs, rna_type, '.fasta.mseq.tsv')
        assert 2 == len(actual)
        assert 2 == len(expected)
        for actual_item in actual:
            assert expected[0] in actual_item or expected[1] in actual_item

    @parameterized.expand([
        ("SSU", 'Taxonomic analysis SSU rRNA'),
        ("LSU", 'Taxonomic analysis LSU rRNA'),
        ("unite", 'Taxonomic analysis UNITE'),
        ("itsonedb", 'Taxonomic analysis ITSoneDB')
    ])
    def test_get_group_type(self, rna_type, expected):

        analysis_result_dirs = dict()
        rootpath = os.path.dirname(__file__).replace('functional', 'test-input')
        analysis_result_dirs['ERR2237853_MERGED_FASTQ'] = os.path.join(rootpath, "ERR2237853_MERGED_FASTQ")
        analysis_result_dirs['ERR2237860_MERGED_FASTQ'] = os.path.join(rootpath, "ERR2237860_MERGED_FASTQ")
        #
        actual = self.test_instance._get_group_type(rna_type)
        assert expected == actual
