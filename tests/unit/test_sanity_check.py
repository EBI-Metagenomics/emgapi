import pytest

import django

django.setup()

from emgapianns.management.lib import sanity_check


def write_file(path, content):
    path.write_text(content, encoding='UTF-8')


class TestSanityCheck:
    def test_amplicon_maindir_results_should_not_raise_exception(self, tmpdir):
        prefix = 'SRR6418294_MERGED_FASTQ'
        write_file(tmpdir / prefix + '.fasta.chunks', 'mydata')
        tmpdir = str(tmpdir)
        cls = sanity_check.AmpliconSanityCheck(tmpdir, prefix)
        cls.check_maindir_results()

    def test_amplicon_maindir_results_should_fail_on_missing_file(self,
                                                                  tmpdir):
        prefix = 'SRR6418294_MERGED_FASTQ'
        tmpdir = str(tmpdir)
        cls = sanity_check.AmpliconSanityCheck(tmpdir, prefix)
        with pytest.raises(AssertionError):
            cls.check_maindir_results()

    @pytest.mark.parametrize('su_types', [
        ('SSU', 'LSU'),
        ('SSU',),
        ('LSU',)
    ])
    def test_amplicon_taxonomy_results_single_subunit(self, su_types, tmpdir):
        prefix = 'SRR6418294_MERGED_FASTQ'
        tax_dir = tmpdir / 'taxonomy-summary'
        tax_dir.mkdir()

        for su_type in su_types:
            path = tax_dir / su_type
            path.mkdir()
            pref = prefix + '_' + su_type
            filelist = sanity_check.AmpliconSanityCheck.taxonomy_result_files
            files = [f.format(pref) for f in filelist]
            for f in files:
                write_file(path / f, 'data')

        tmpdir = str(tmpdir)
        cls = sanity_check.AmpliconSanityCheck(tmpdir, prefix)
        with pytest.raises(AssertionError):
            cls.check_taxonomy_results()

    def test_amplicon_taxonomy_results_should_fail_on_missing_file(self,
                                                                   tmpdir):
        prefix = 'SRR6418294_MERGED_FASTQ'
        tmpdir = str(tmpdir)
        cls = sanity_check.AmpliconSanityCheck(tmpdir, prefix)
        with pytest.raises(AssertionError):
            cls.check_taxonomy_results()
