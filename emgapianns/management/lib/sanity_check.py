import os
from glob import glob


def get_missing_filelist(expected, real):
    return ", ".join(expected.difference(real))


def get_dir_files(d):
    listing = glob(os.path.join(d, '*'))
    files = filter(os.path.isfile, listing)
    names = map(os.path.basename, files)
    return set(names)


def check_content_match(expected_files, result_dir_files):
    if expected_files != result_dir_files:
        missing_files = get_missing_filelist(expected_files,
                                             result_dir_files)
        raise AssertionError('{} are missing'.format(missing_files))


class BasicSanityCheck:
    result_files = [
    ]

    taxonomy_subdirs = {'SSU', 'LSU'}
    taxonomy_result_files = {
        'krona.html',
        'kingdom-counts.txt',
        '{}.fasta.mseq.tsv',
        '{}.fasta.mseq.gz',
        '{}.fasta.mseq_hdf5.biom',
        '{}.fasta.mseq_json.biom',
    }
    flag_files = [
        ''
    ]

    extra_files = []

    def __init__(self, d, prefix):
        self.dir = d
        self.prefix = prefix
        if hasattr(self, 'extra_files'):
            self.result_files.extend(getattr(self, 'extra_files'))

        assert len(self.result_files) > 0
        assert len(self.flag_files) > 0

    def gen_result_files(self, filelist, prefix=None):
        prefix = prefix or self.prefix
        return {f.format(prefix) for f in filelist}

    def check_maindir_results(self):
        expected_files = self.gen_result_files(self.result_files)
        result_dir_files = get_dir_files(self.dir)
        check_content_match(expected_files, result_dir_files)

    def check_taxonomy_results(self):
        tax_dir = os.path.join(self.dir, 'taxonomy-summary')
        if not os.path.exists(tax_dir):
            raise AssertionError('taxonomy-summary dir is missing')

        subunit_dirs = os.listdir(tax_dir)
        for su_type in subunit_dirs:
            subdir = os.path.join(tax_dir, su_type)
            self.check_taxonomy(subdir, su_type)
        else:
            raise AssertionError('No SSU/LSU dir found in taxonomy-summary')

    def check_taxonomy(self, subdir, su_type):
        prefix = self.prefix + '_' + su_type
        expected_files = self.gen_result_files(self.taxonomy_result_files, prefix)
        tax_dir_content = get_dir_files(subdir)
        check_content_match(expected_files, tax_dir_content)

    def check(self):
        self.check_maindir_results()
        self.check_taxonomy_results()


class AmpliconSanityCheck(BasicSanityCheck):
    taxonomy_subdirs = {'SSU'}
    extra_files = [
        '{}.fasta.chunks',
    ]


class WgsSanityCheck(BasicSanityCheck):
    extra_files = []


def run_sanity_check(d, job_prefix, lib_strategy):
    lib_cls = {
        'AMPLICON': AmpliconSanityCheck,
        'WGS': WgsSanityCheck,
        'ASSEMBLY': WgsSanityCheck,
        'OTHER': WgsSanityCheck
    }
    cls = lib_cls[lib_strategy]
    return cls(d, job_prefix).check()
