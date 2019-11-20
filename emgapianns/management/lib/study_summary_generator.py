import logging
import os
import sys
from pathlib import Path
from subprocess import check_output, CalledProcessError

import numpy as np
import pandas as pd

from emgapianns.management.lib import utils
from emgapi import models as emg_models
from django.db.models import Q


class StudySummaryGenerator(object):

    def __init__(self, accession, pipeline, rootpath, database):
        self.study_accession = accession
        self.pipeline = pipeline
        self.rootpath = rootpath
        self.emg_db_name = database
        self.study = emg_models.Study.objects.using(self.emg_db_name).get(secondary_accession=self.study_accession)
        self.study_result_dir = os.path.join(self.rootpath, self.study.result_directory)
        self.summary_dir = None

    def run(self):
        if not os.path.exists(self.study_result_dir):
            sys.exit(
                f"Study result directory for {self.study_accession} does not exist:\n{self.study_result_dir}")

        jobs = emg_models.AnalysisJob.objects.using(self.emg_db_name)
        jobs = jobs.filter(
            Q(study__secondary_accession=self.study_accession) &
            Q(analysis_status__analysis_status='completed') &
            Q(pipeline__release_version=self.pipeline))

        experiment_types = set()
        analysis_result_dirs = {}
        for job in jobs:
            job_result_directory = os.path.join(self.rootpath, job.result_directory)
            job_input_file_name = job.input_file_name
            analysis_result_dirs[job_input_file_name] = job_result_directory
            experiment_types.add(job.experiment_type.experiment_type)

        self.summary_dir = os.path.join(self.study_result_dir, 'version_{}/project-summary'.format(self.pipeline))
        self.create_summary_dir()

        # TODO: Add UNITE and ITSoneDB
        if self.pipeline == '4.1':
            self.generate_taxonomy_phylum_summary(analysis_result_dirs, self.pipeline, 'SSU',
                                                  'phylum_taxonomy_abundances_SSU_v{}.tsv'.format(self.pipeline))
            self.generate_taxonomy_phylum_summary(analysis_result_dirs, self.pipeline, 'LSU',
                                                  f'phylum_taxonomy_abundances_LSU_v{self.pipeline}.tsv')

        self.generate_taxonomy_summary(analysis_result_dirs, 'SSU',
                                       'taxonomy_abundances_SSU_v{}.tsv'.format(self.pipeline))
        self.generate_taxonomy_summary(analysis_result_dirs, 'LSU',
                                       'taxonomy_abundances_LSU_v{}.tsv'.format(self.pipeline))

        if len(experiment_types) == 1 and 'amplicon' in experiment_types:
            logging.info("AMPLICON datasets only! Skipping the generation of the functional matrix files!")
        else:
            self.generate_ipr_summary(analysis_result_dirs, 'IPR_abundances_v{}.tsv'.format(self.pipeline))
            self.generate_go_summary(analysis_result_dirs, 'slim')
            self.generate_go_summary(analysis_result_dirs, 'full')

        logging.info("Program finished successfully.")

    def generate_taxonomy_phylum_summary(self, analysis_result_dirs, version, su_type, filename):
        if version == '4.1':
            self.generate_taxonomy_phylum_summary_v4(analysis_result_dirs, su_type, filename)
        else:
            self.generate_taxonomy_phylum_summary_v5(analysis_result_dirs, su_type, filename)

    def generate_taxonomy_phylum_summary_v4(self, analysis_result_dirs, su_type, filename):
        res_files = self.get_kingdom_counts_files(analysis_result_dirs, su_type)

        study_df = self.merge_dfs(res_files,
                                  delimiter='\t',
                                  key=['kingdom', 'phylum'],
                                  raw_cols=['kingdom', 'phylum', 'count', 'ignored'])

        if len(study_df.index) > 0:
            self.write_results_file(study_df, filename)

            alias = '{}_phylum_taxonomy_abundances_{}_v{}.tsv'.format(self.study_accession, su_type, self.pipeline)
            description = 'Phylum level taxonomies {}'.format(su_type)
            group = 'Taxonomic analysis {} rRNA'.format(su_type)
            self.upload_study_file(filename, alias, description, group)

    def generate_taxonomy_phylum_summary_v5(self, analysis_result_dirs, su_type, filename):
        # Fixme: Work in progress! Finish implementation
        res_files = self.get_mapseq_result_files(analysis_result_dirs, su_type, '.fasta.mseq.gz')

        study_df = self.merge_dfs(res_files,
                                  delimiter='\t',
                                  key=['kingdom', 'phylum'],
                                  raw_cols=['kingdom', 'phylum', 'count', 'ignored'])

        if len(study_df.index) > 0:
            self.write_results_file(study_df, filename)

            alias = '{}_phylum_taxonomy_abundances_{}_v{}.tsv'.format(self.study_accession, su_type, self.pipeline)
            description = 'Phylum level taxonomies {}'.format(su_type)
            group = 'Taxonomic analysis {} rRNA'.format(su_type)
            self.upload_study_file(filename, alias, description, group)

    def generate_taxonomy_summary(self, analysis_result_dirs, su_type, filename):
        res_files = self.get_mapseq_result_files(analysis_result_dirs, su_type, '.fasta.mseq.tsv')
        study_df = self.merge_dfs(res_files,
                                  key=['lineage'],
                                  delimiter='\t',
                                  raw_cols=['OTU', 'count', 'lineage'],
                                  skip_rows=2)
        study_df = study_df.rename(columns={'lineage': '#SampleID'})

        if len(study_df.index) > 0:
            self.write_results_file(study_df, filename)

            alias = '{}_taxonomy_abundances_{}_v{}.tsv'.format(self.study_accession, su_type, self.pipeline)
            description = 'Taxonomic assignments {}'.format(su_type)
            group = 'Taxonomic analysis {} rRNA'.format(su_type)
            self.upload_study_file(filename, alias, description, group)

    def get_raw_result_files(self, res_file_re):
        paths = list(Path(self.study_result_dir).glob(res_file_re))
        return [str(p.resolve()) for p in paths]

    def merge_dfs(self, filelist, delimiter, key, raw_cols, skip_rows=0):
        study_df = pd.DataFrame(columns=key)
        for f in sorted(filelist):
            accession = utils.get_accession_from_result_dir_path(f)
            df = self.read_count_tsv(f, delimiter, raw_cols, skip_rows)
            df = df.filter(key + ['count'])
            df = df.rename(columns={'count': accession})
            study_df = study_df.merge(df, on=key, how='outer')
        study_df = study_df.sort_values(by=key)
        study_df = self.clean_summary_df(study_df)
        return study_df

    def generate_ipr_summary(self, analysis_result_dirs, filename):
        res_files = self.get_ipr_result_files(analysis_result_dirs)
        study_df = self.merge_dfs(res_files, delimiter=',',
                                  key=['IPR', 'description'],
                                  raw_cols=['IPR', 'description', 'count'])

        if len(study_df.index) > 0:
            self.write_results_file(study_df, filename)

            alias = '{}_IPR_abundances_v{}.tsv'.format(self.study_accession, self.pipeline)
            description = 'InterPro matches'
            self.upload_study_file(filename, alias, description, 'Functional analysis')

    def generate_go_summary(self, analysis_result_dirs, mode):
        if mode == 'slim':
            sum_file = 'GO-slim'
            description = 'GO slim annotation'
        else:
            sum_file = 'GO'
            description = 'Complete GO annotation'

        res_files = self.get_go_result_files(analysis_result_dirs, mode)
        study_df = self.merge_dfs(res_files, delimiter=',',
                                  key=['GO', 'description', 'category'],
                                  raw_cols=['GO', 'description', 'category', 'count'])
        study_df['description'] = study_df['description'].str.replace(',', '@')
        study_df['category'] = study_df['category'].str.replace('_', ' ')
        realname = sum_file + '_abundances_v{}.tsv'.format(self.pipeline)

        if len(study_df.index) > 0:
            self.write_results_file(study_df, realname)

            self.generate_filtered_go_summary(study_df,
                                              'category == "cellular component"',
                                              'CC_{}_abundances_v{}.tsv'.format(sum_file, self.pipeline))

            self.generate_filtered_go_summary(study_df,
                                              'category == "biological process"',
                                              'BP_{}_abundances_v{}.tsv'.format(sum_file, self.pipeline))

            self.generate_filtered_go_summary(study_df,
                                              'category not in ["biological process", "cellular component"]',
                                              'MF_{}_abundances_v{}.tsv'.format(sum_file, self.pipeline))

            alias = '{}_{}_abundances_v{}.tsv'.format(self.study_accession, sum_file, self.pipeline)
            self.upload_study_file(realname, alias, description, 'Functional analysis')
            return study_df

    def generate_filtered_go_summary(self, df, query, filename):
        df = df.query(query)
        self.write_results_file(df, filename)

    @staticmethod
    def read_count_tsv(filename, delimiter, cols, skip_rows=0):
        df = pd.read_csv(filename, delimiter=delimiter, names=cols, skiprows=skip_rows)
        df = df.astype({'count': 'int'})
        return df

    def write_results_file(self, df, filename):
        filepath = os.path.join(self.summary_dir, filename)
        df.to_csv(filepath, sep='\t', header=True, index=False)

    @staticmethod
    def clean_summary_df(df):
        df = df.fillna(0)
        int_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        df = df.astype({col: 'int' for col in int_cols})
        return df

    def create_summary_dir(self):
        os.makedirs(self.summary_dir, exist_ok=True)

    def upload_study_file(self, realname, alias, description, group):
        file_config = {
            'alias': alias,
            'compression': False,
            'description_label': description,
            'format_name': 'TSV',
            'group_type': group,
            'real_name': realname,
            'subdir': 'version_{}/project-summary'.format(self.pipeline),
            '_required': True
        }
        _study_rootpath = self.study_result_dir.replace('version_{}'.format(self.pipeline), '')
        utils.StudyDownload(self.emg_db_name, _study_rootpath, file_config, self.pipeline).save(self.study)

    @staticmethod
    def get_mapseq_result_files(analysis_result_dirs, su_type, mapseq_file_extension):
        result = []
        for input_file_name, dir in analysis_result_dirs.items():
            res_file_re = os.path.join(dir, 'taxonomy-summary', su_type,
                                       '{}_{}{}'.format(input_file_name, su_type, mapseq_file_extension))
            if os.path.exists(res_file_re):
                result.append(res_file_re)
            else:
                logging.warning("Result file does not exist:\n{}".format(res_file_re))
        return result

    @staticmethod
    def get_kingdom_counts_files(analysis_result_dirs, su_type):
        result = []
        for input_file_name, dir in analysis_result_dirs.items():
            res_file_re = os.path.join(dir, 'taxonomy-summary', su_type, 'kingdom-counts.txt')
            if os.path.exists(res_file_re):
                result.append(res_file_re)
            else:
                logging.warning("Result file does not exist:\n{}".format(res_file_re))
        return result

    @staticmethod
    def get_ipr_result_files(analysis_result_dirs):
        result = []
        for input_file_name, dir in analysis_result_dirs.items():
            res_file_re = os.path.join(dir, '{}_summary.ipr'.format(input_file_name))
            if os.path.exists(res_file_re):
                result.append(res_file_re)
            else:
                logging.warning("Result file does not exist:\n{}".format(res_file_re))
        return result

    @staticmethod
    def get_go_result_files(analysis_result_dirs, mode):
        result = []
        for input_file_name, dir in analysis_result_dirs.items():
            file_name = '{}_summary.go' if mode == 'full' else '{}_summary.go_slim'
            res_file_re = os.path.join(dir, file_name.format(input_file_name))
            if os.path.exists(res_file_re):
                result.append(res_file_re)
            else:
                logging.warning("Result file does not exist:\n{}".format(res_file_re))
        return result

    @staticmethod
    def __get_phylum_counts(filepath):
        """
            Summarises the counts for each unique phylum.
        :return:
        """
        std_out = check_output(
            "zcat ERR3506537_MERGED_FASTQ_SSU.fasta.mseq.gz | grep -v '^#' | cut -f 14- | cut -d ';' -f 1-3 | sed 's/\t$//' | sed 's/;p__$//' | sed 's/;k__$//' | sort | uniq -c".format(
                filepath), shell=True).rstrip()
        return std_out

    @staticmethod
    def __parse_phylum_counts(std_out):
        """
            Parse the standard output of the Linux oneliner.
        :return:
        """
        # TODO: Implement
        pass

    @staticmethod
    def __count_number_of_lines(filepath):
        """
            Counts number of lines in compressed text file.
        :return:
        """
        count = check_output("zcat {} | wc -l".format(filepath), shell=True).rstrip()
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
