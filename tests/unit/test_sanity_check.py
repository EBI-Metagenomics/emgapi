# FIXME: update!
import os
from unittest.mock import patch
import pytest

from emgapianns.management.lib import sanity_check  # noqa: E402


def write_file(path, content):
    path.write_text(content, encoding='UTF-8')


def gen_all_tax_files(su_types, tmpdir, prefix):
    tax_dir = tmpdir / 'taxonomy-summary'
    tax_dir.mkdir()

    for su_type in su_types:
        path = tax_dir / su_type
        path.mkdir()
        pref = prefix + '_' + su_type
        filelist = sanity_check.SanityCheck.taxonomy_result_files
        files = [f.format(pref) for f in filelist]
        for f in files:
            write_file(path / f, 'data')


def gen_all_flag_files(tmpdir):
    filelist = sanity_check.SanityCheck.flag_files
    for f in filelist:
        write_file(tmpdir / f, 'data')


def gen_all_qc_files(tmpdir):
    qc_dir = tmpdir / 'qc-statistics'
    qc_dir.mkdir()

    filelist = sanity_check.SanityCheck.qc_files
    for f in filelist:
        write_file(qc_dir / f, 'data')


def gen_all_maindir_files(tmpdir, prefix):
    filelist = sanity_check.SanityCheck.result_files
    files = [f.format(prefix) for f in filelist]
    for f in files:
        write_file(tmpdir / f, 'data')
    write_file(tmpdir / prefix + '.fasta.chunks', 'mydata')


def gen_all_seqdir_files(tmpdir):
    seq_dir = tmpdir / 'sequence-categorisation'
    seq_dir.mkdir()
    filelist = sanity_check.SanityCheck.seq_categorisation
    for f in filelist:
        write_file(seq_dir / f, 'data')


class TestSanityCheck:

    @patch('os.path.basename')
    def test_sanitycheck_initialisation(self, mock_dir):
        mock_dir.return_value = "test"
        expected_accession = "ERRXXXXXX"
        experiment_type = 'amplicon'
        version = '4.1'
        expected_result_dir = "/tmp"
        test_instance = sanity_check.SanityCheck(expected_accession, expected_result_dir, experiment_type, version)
        assert expected_accession == test_instance.accession
        assert expected_result_dir == test_instance.dir
        assert mock_dir.return_value == test_instance.prefix
        config = test_instance.config
        assert config is not None
        assert isinstance(config, list)
        assert len(config) > 0
        file = config[0]
        assert isinstance(file, dict)
        assert len(file) > 0
        assert "_required" in file
        assert "blah" not in file

    def test_sanity_check_version_4_results_succeeds(self):
        accession = 'ERR2985769'
        experiment_type = 'amplicon'
        version = '4.1'
        root_dir = os.path.dirname(__file__).replace('unit', 'test-input')
        result_dir = os.path.join(root_dir, 'results/2019/08/ERP112711/version_4.1/ERR298/ERR2985769_MERGED_FASTQ')
        test_instance = sanity_check.SanityCheck(accession, result_dir, experiment_type, version)
        test_instance.check_all()

    def test_sanity_check_version_4_results_raise_exception(self):
        accession = 'ERR2985769'
        experiment_type = 'amplicon'
        version = '4.1'
        root_dir = os.path.dirname(__file__).replace('unit', 'test-input')
        result_dir = os.path.join(root_dir, 'no-results')
        test_instance = sanity_check.SanityCheck(accession, result_dir, experiment_type, version)
        with pytest.raises(FileNotFoundError):
            test_instance.check_all()

    # def test_amplicon_maindir_results_should_not_raise_exception(self, tmpdir):
    #     accession = None
    #     experiment_type = 'amplicon'
    #     version = None
    #     prefix = 'SRR6418294_MERGED_FASTQ'
    #     gen_all_maindir_files(tmpdir, prefix)
    #     result_dir = str(tmpdir)
    #     cls = sanity_check.SanityCheck(accession, result_dir, experiment_type, version)
    #     cls.check_maindir_results()
    #
    # def test_amplicon_maindir_results_should_raise_error_on_missing_file(self, tmpdir):
    #     prefix = 'SRR6418294_MERGED_FASTQ'
    #     tmpdir = str(tmpdir)
    #     cls = sanity_check.SanityCheck(tmpdir, prefix)
    #     with pytest.raises(AssertionError):
    #         cls.check_maindir_results()
    #
    # @pytest.mark.parametrize('su_types', [
    #     ('SSU', 'LSU'),
    #     ('SSU',),
    #     ('LSU',)
    # ])
    # def test_amplicon_taxonomy_results_varying_subunit(self, su_types, tmpdir):
    #     prefix = 'SRR6418294_MERGED_FASTQ'
    #     gen_all_tax_files(su_types, tmpdir, prefix)
    #     tmpdir = str(tmpdir)
    #     cls = sanity_check.SanityCheck(tmpdir, prefix)
    #     cls.check_taxonomy_results()
    #
    # def test_amplicon_taxonomy_results_missing_subunits(self, tmpdir):
    #     prefix = 'SRR6418294_MERGED_FASTQ'
    #     tax_dir = tmpdir / 'taxonomy-summary'
    #     tax_dir.mkdir()
    #
    #     tmpdir = str(tmpdir)
    #     cls = sanity_check.SanityCheck(tmpdir, prefix)
    #     with pytest.raises(AssertionError):
    #         cls.check_taxonomy_results()
    #
    # def test_amplicon_taxonomy_results_should_raise_error_on_missing_tax_dir(self, tmpdir):
    #     prefix = 'SRR6418294_MERGED_FASTQ'
    #     tmpdir = str(tmpdir)
    #     cls = sanity_check.SanityCheck(tmpdir, prefix)
    #     with pytest.raises(AssertionError):
    #         cls.check_taxonomy_results()
    #
    # def test_check_qc_should_raise_error_on_missing_dir(self, tmpdir):
    #     prefix = 'SRR6418294_MERGED_FASTQ'
    #     tmpdir = str(tmpdir)
    #     cls = sanity_check.SanityCheck(tmpdir, prefix)
    #     with pytest.raises(AssertionError):
    #         cls.check_qc_results()
    #
    # def test_qc(self, tmpdir):
    #     prefix = 'SRR6418294_MERGED_FASTQ'
    #     gen_all_qc_files(tmpdir)
    #
    #     tmpdir = str(tmpdir)
    #     cls = sanity_check.SanityCheck(tmpdir, prefix)
    #     cls.check_qc_results()
    #
    # def test_check_flags(self, tmpdir):
    #     prefix = 'SRR6418294_MERGED_FASTQ'
    #     gen_all_flag_files(tmpdir)
    #     tmpdir = str(tmpdir)
    #     cls = sanity_check.SanityCheck(tmpdir, prefix)
    #     cls.check_flags()
    #
    # def test_check_flags_should_raise_error_on_missing_flags(self, tmpdir):
    #     prefix = 'SRR6418294_MERGED_FASTQ'
    #     tmpdir = str(tmpdir)
    #     cls = sanity_check.SanityCheck(tmpdir, prefix)
    #     with pytest.raises(AssertionError):
    #         cls.check_flags()
    #
    # def test_check_seqdir(self, tmpdir):
    #     prefix = 'SRR6418294_MERGED_FASTQ'
    #     gen_all_seqdir_files(tmpdir)
    #     tmpdir = str(tmpdir)
    #     cls = sanity_check.SanityCheck(tmpdir, prefix)
    #     cls.check_seq_categorisation()
    #
    # def test_check_seqdir_should_raise_error_on_missing_flags(self, tmpdir):
    #     prefix = 'SRR6418294_MERGED_FASTQ'
    #     tmpdir = str(tmpdir)
    #     cls = sanity_check.SanityCheck(tmpdir, prefix)
    #     with pytest.raises(AssertionError):
    #         cls.check_seq_categorisation()
    #
    # def test_check_all_should_raise_error_on_missing_files(self, tmpdir):
    #     prefix = 'SRR6418294_MERGED_FASTQ'
    #     tmpdir = str(tmpdir)
    #     cls = sanity_check.SanityCheck(tmpdir, prefix)
    #     with pytest.raises(AssertionError):
    #         cls.check_all()
    #
    # def test_check_all_should_work_on_valid_dir(self, tmpdir):
    #     prefix = 'SRR6418294_MERGED_FASTQ'
    #     gen_all_seqdir_files(tmpdir)
    #     gen_all_maindir_files(tmpdir, prefix)
    #     gen_all_qc_files(tmpdir)
    #     gen_all_tax_files(['SSU', 'LSU'], tmpdir, prefix)
    #     gen_all_flag_files(tmpdir)
    #     tmpdir = str(tmpdir)
    #     cls = sanity_check.SanityCheck(tmpdir, prefix)
    #     cls.check_all()
    #
    # def test_run_sanity_check_should_raise_error_on_missing_files(self, tmpdir):
    #     prefix = 'SRR6418294_MERGED_FASTQ'
    #     tmpdir = str(tmpdir)
    #     with pytest.raises(AssertionError):
    #         sanity_check.run_sanity_check(tmpdir, prefix, 'AMPLICON')
    #
    # def test_run_sanity_check_should_pass(self, tmpdir):
    #     prefix = 'SRR6418294_MERGED_FASTQ'
    #     gen_all_seqdir_files(tmpdir)
    #     gen_all_maindir_files(tmpdir, prefix)
    #     gen_all_qc_files(tmpdir)
    #     gen_all_tax_files(['SSU', 'LSU'], tmpdir, prefix)
    #     gen_all_flag_files(tmpdir)
    #     tmpdir = str(tmpdir)
    #     sanity_check.run_sanity_check(tmpdir, prefix, 'AMPLICON')
