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
    missing_files = get_missing_filelist(expected_files, result_dir_files)
    if missing_files:
        raise AssertionError('{} are missing'.format(missing_files))


class BasicSanityCheck:
    result_files = {
        '{}_CDS_annotated.faa.chunks',
        '{}_CDS_annotated.faa.gz',
        '{}_CDS_annotated.ffn.chunks',
        '{}_CDS_annotated.ffn.gz',
        '{}_CDS_unannotated.faa.chunks',
        '{}_CDS_unannotated.faa.gz',
        '{}_CDS_unannotated.ffn.chunks',
        '{}_CDS_unannotated.ffn.gz',
        '{}.cmsearch.all.tblout.deoverlapped.gz',
        '{}.cmsearch.all.tblout.gz',
        '{}.fasta.chunks',
        '{}.fasta.gz',
        '{}.fasta.submitted.count',
        '{}_I5.tsv.chunks',
        '{}_I5.tsv.gz',
        '{}_run.err',
        '{}_run.log',
        '{}_summary',
        '{}_summary.go',
        '{}_summary.go_slim',
        '{}_summary.ipr',
        '{}_summary.rfam',
        'globalsummary.out',
        'go-summary.out',
        'README',
        'RESOURCE_USAGE_PROFILE'
    }

    taxonomy_subdirs = {
        'SSU', 'LSU'
    }

    taxonomy_result_files = {
        'krona.html',
        'kingdom-counts.txt',
        '{}.fasta.mseq.tsv',
        '{}.fasta.mseq.txt',
        '{}.fasta.mseq.gz',
        '{}.fasta.mseq_hdf5.biom',
        '{}.fasta.mseq_json.biom',
    }

    qc_files = {
        'GC-distribution.out.full',
        'GC-distribution.out.full_bin',
        'GC-distribution.out.full_pcbin',
        'nucleotide-distribution.out.full',
        'seq-length.out.full',
        'seq-length.out.full_bin',
        'seq-length.out.full_pcbin',
        'summary.out'
    }
    flag_files = {
        'stepCDS-success',
        'stepChunkingAndCompression-success',
        'stepCMSearchDeoverlap-success',
        'stepCMSearch-success',
        'stepDecompression-success',
        'stepFastaHeaderClean-success',
        'stepFinalCleaning-success',
        'stepGOSummary-success',
        'stepI5tsv-success',
        'stepInit-success',
        'stepMAPseq-success',
        'stepNewCharts-success',
        'stepQCStats-success',
        'stepRNASelection-success',
        'stepRNASummary-success',
        'stepSequenceCategorisation-success',
        'stepSummary-success',
        'stepTaxonomySummary-success',
        'sync-success'
    }

    seq_categorisation = {
        'interproscan.fasta.chunks',
        'interproscan.fasta.gz',
        'LSU.fasta.chunks',
        'LSU.fasta.gz',
        'noFunction.fasta.chunks',
        'noFunction.fasta.gz',
        'pCDS.fasta.chunks',
        'pCDS.fasta.gz',
        'SSU.fasta.chunks',
        'SSU.fasta.gz'
    }

    def __init__(self, d, prefix):
        self.dir = d
        self.prefix = prefix
        if hasattr(self, 'extra_files'):
            self.result_files.union(getattr(self, 'extra_files'))

        assert len(self.result_files) > 0
        assert len(self.flag_files) > 0

    def gen_result_files(self, filelist, prefix=None):
        prefix = prefix or self.prefix
        return {f.format(prefix) for f in filelist}

    def check_flags(self):
        self.check_dir_content(self.dir, self.flag_files)

    def check_maindir_results(self):
        self.check_dir_content(self.dir, self.result_files)

    def check_taxonomy_results(self):
        tax_dir = os.path.join(self.dir, 'taxonomy-summary')
        if not os.path.exists(tax_dir):
            raise AssertionError('taxonomy-summary dir is missing')

        subunit_dirs = os.listdir(tax_dir)

        if len(subunit_dirs) == 0:
            raise AssertionError('No SSU/LSU dir found in taxonomy-summary')

        for su_type in subunit_dirs:
            subdir = os.path.join(tax_dir, su_type)
            prefix = self.prefix + '_' + su_type
            self.check_dir_content(subdir, self.taxonomy_result_files, prefix=prefix)

    def check_qc_results(self):
        dirpath = os.path.join(self.dir, 'qc-statistics')
        self.check_dir_content(dirpath, self.qc_files)

    def check_seq_categorisation(self):
        dirpath = os.path.join(self.dir, 'sequence-categorisation')
        self.check_dir_content(dirpath, self.seq_categorisation)

    def check_dir_content(self, dirpath, content, prefix=None):
        expected_files = self.gen_result_files(content, prefix)
        if not os.path.exists(dirpath):
            raise AssertionError('Missing directory {}'.format(dirpath))
        result_dir_files = get_dir_files(dirpath)
        check_content_match(expected_files, result_dir_files)

    def check_all(self):
        # self.check_flags()
        self.check_maindir_results()
        self.check_taxonomy_results()
        self.check_qc_results()
        self.check_seq_categorisation()


class AmpliconSanityCheck(BasicSanityCheck):
    extra_files = {}


class WgsSanityCheck(BasicSanityCheck):
    extra_files = {}


def run_sanity_check(d, job_prefix, lib_strategy):
    lib_cls = {
        'AMPLICON': AmpliconSanityCheck,
        'WGS': WgsSanityCheck,
        'ASSEMBLY': WgsSanityCheck,
        'OTHER': WgsSanityCheck
    }
    cls = lib_cls[lib_strategy]
    return cls(d, job_prefix).check_all()
