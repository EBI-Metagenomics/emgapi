import collections
import logging
import os
import subprocess
import sys
from pathlib import Path
from subprocess import check_output, CalledProcessError

import numpy as np
import pandas as pd
from django.db.models import Q

from emgapi import models as emg_models
from emgapianns.management.lib import utils
from emgapianns.management.lib.utils import DownloadFileDatabaseHandler


class StudySummaryGenerator(object):

    def __init__(self, accession, pipeline, rootpath, nfs_public_rootpath, database):
        self.study_accession = accession
        self.pipeline = pipeline
        self.rootpath = rootpath
        self.nfs_public_rootpath = nfs_public_rootpath
        self.emg_db_name = database
        self.study = emg_models.Study.objects.using(self.emg_db_name).get(secondary_accession=self.study_accession)
        self.study_result_dir = os.path.join(self.rootpath, self.study.result_directory)
        self.summary_dir = None
        self.MAPSEQ_COLUMN_MAPPER = {'SSU': 'SILVA', 'LSU': 'SILVA', 'unite': 'UNITE', 'itsonedb': 'ITSone'}

    def run(self):
        if not os.path.exists(self.study_result_dir):
            sys.exit(
                "Study result directory for {} does not exist:\n{}".format(self.study_accession, self.study_result_dir))

        jobs = emg_models.AnalysisJob.objects.using(self.emg_db_name)
        jobs = jobs.filter(
            Q(study__secondary_accession=self.study_accession) &
            Q(analysis_status__analysis_status='completed') &
            Q(pipeline__release_version=self.pipeline))

        experiment_types = set()
        analysis_jobs = {}
        for job in jobs:
            job_result_directory = os.path.join(self.rootpath, job.result_directory)
            job_input_file_name = job.input_file_name
            analysis_jobs[job_input_file_name] = job_result_directory
            experiment_types.add(job.experiment_type.experiment_type)

        self.summary_dir = os.path.join(self.study_result_dir, 'version_{}/project-summary'.format(self.pipeline))
        self.create_summary_dir()

        for rna_types in self.MAPSEQ_COLUMN_MAPPER.keys():
            self.generate_taxonomy_phylum_summary(analysis_jobs, self.pipeline, '{}'.format(rna_types),
                                                  'phylum_taxonomy_abundances_{}_v{}.tsv'.format(rna_types,
                                                                                                 self.pipeline))
            self.generate_taxonomy_summary(analysis_jobs, '{}'.format(rna_types),
                                           'taxonomy_abundances_{}_v{}.tsv'.format(rna_types, self.pipeline))

        if len(experiment_types) == 1 and 'amplicon' in experiment_types:
            logging.info("AMPLICON datasets only! Skipping the generation of the functional matrix files!")
        else:
            self.generate_ipr_summary(analysis_jobs, 'IPR_abundances_v{}.tsv'.format(self.pipeline))
            self.generate_go_summary(analysis_jobs, 'slim')
            self.generate_go_summary(analysis_jobs, 'full')

        self.sync_study_summary_files()

        logging.info("Program finished successfully.")

    def sync_study_summary_files(self):
        logging.info("Syncing project summary files over to NFS public...")
        _study_result_dir = self.study.result_directory
        nfs_prod_dest = os.path.join(self.rootpath, _study_result_dir,
                                     'version_{}/{}'.format(self.pipeline, 'project-summary'))
        nfs_public_dest = os.path.join(self.nfs_public_rootpath, _study_result_dir, 'version_{}/'.format(self.pipeline))
        logging.info("From: " + nfs_prod_dest)
        logging.info("To: " + nfs_public_dest)

        rsync_options = ['-rtDzv']

        more_rsync_options = ['--no-owner', '--no-perms', '--prune-empty-dirs', '--exclude', '*.lsf',
                              '--delete-excluded', '--chmod=Do-w,Fu+x,Fg+x,Fo+r']
        rsync_cmd = ["sudo", "-H", "-u", "emg_adm", "rsync"] + rsync_options + more_rsync_options + [nfs_prod_dest,
                                                                                                     nfs_public_dest]
        logging.info(rsync_cmd)

        subprocess.check_call(rsync_cmd)
        logging.info("Synchronisation is done.")

    def generate_taxonomy_phylum_summary(self, analysis_jobs, version, su_type, filename):

        study_df = None
        if version == '4.1':
            study_df = self.generate_taxonomy_phylum_summary_v4(analysis_jobs, su_type)
        elif version == '5.0':
            study_df = self.generate_taxonomy_phylum_summary_v5(analysis_jobs, su_type)
        else:
            logging.warning("Pipeline version {} not supported yet!".format(version))
            pass

        if study_df and len(study_df.index) > 0:
            self.write_results_file(study_df, filename)

            alias = '{}_phylum_taxonomy_abundances_{}_v{}.tsv'.format(self.study_accession, su_type, self.pipeline)
            description = 'Phylum level taxonomies {}'.format(su_type)
            group = 'Taxonomic analysis {} rRNA'.format(su_type)
            self.upload_study_file(filename, alias, description, group)

    def generate_taxonomy_phylum_summary_v4(self, analysis_result_dirs, su_type):
        res_files = self.get_kingdom_counts_files(analysis_result_dirs, su_type)

        study_df = self.merge_dfs(res_files,
                                  delimiter='\t',
                                  key=['kingdom', 'phylum'],
                                  raw_cols=['kingdom', 'phylum', 'count', 'ignored'])

        return study_df

    def generate_taxonomy_phylum_summary_v5(self, analysis_jobs, rna_type):
        job_data_frames = dict()
        # Iterate over each run
        for acc, result_directory in analysis_jobs.items():
            # Define results files and for each result file perform necessary operations
            if rna_type in ['unite', 'itsonedb']:
                sequence_file = self.__get_rna_fasta_file(result_directory, 'ITS_masked.fasta.gz')
            else:  # for SILVA: LSU and SSU
                sequence_file = self.__get_rna_fasta_file(result_directory, '{}.fasta.gz'.format(rna_type))
            if not sequence_file:
                continue
            num_rna_seqs = self.__count_number_of_seqs(sequence_file)
            #
            mapseq_result_file = self.__get_mapseq_result_file(acc, result_directory, rna_type, '.fasta.mseq.gz')
            if not mapseq_result_file:
                continue
            phylum_count_data = self.__parse_phylum_counts_v5(mapseq_result_file, num_rna_seqs, rna_type)

            job_df = self.__build_dataframe(phylum_count_data)
            job_data_frames[acc] = job_df

        study_df = self.merge_dfs_v5(job_data_frames,
                                     delimiter='\t',
                                     key=['superkingdom', 'kingdom', 'phylum'],
                                     raw_cols=['kingdom', 'kingdom', 'phylum', 'count', 'ignored'])

        return study_df

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

    def merge_dfs_v5(self, dataframes, delimiter, key, raw_cols, skip_rows=0):
        study_df = pd.DataFrame(columns=key)

        for accession, df in dataframes.items():
            df = df.filter(key + ['count'])
            df = df.rename(columns={'count': accession})
            study_df = study_df.merge(df, on=key, how='outer')
        study_df = study_df.sort_values(by=key)
        study_df = self.clean_summary_df(study_df)
        return study_df

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

    def __parse_phylum_counts_v5(self, mapseq_file, num_rna_seqs, rna_type, delimiter='\t', compression='gzip',
                                 header=1):
        """
            Get phylum counts for v5 results.

            Implementation of the following linux command using pandas dataframe and collections:
            zcat SRR6028649_MERGED_FASTQ_SSU.fasta.mseq.gz | grep -v "^#" | cut -f 14- | cut -d ";" -f 1-3 | sed 's/\t$//' | sed 's/;p__$//' | sed 's/;k__$//' | sort | uniq -c
        :return:
        """
        unassigned = 'Unassigned'
        # column header keywords: UNITE, ITSone, SILVA
        column_name = self.MAPSEQ_COLUMN_MAPPER.get(rna_type)
        df = pd.read_csv(mapseq_file, compression=compression, header=header, sep=delimiter)

        taxonomies = list()
        for i, row in df.iterrows():
            value = df.at[i, column_name]
            index = value.find(";c__")
            if index > 0:
                value = value[0:index]
            value = self.normalize_taxa_hierarchy(value)
            taxonomies.append(value)

        counter = 1
        data = dict()
        for phylum, count in collections.Counter(taxonomies).items():
            new_columns = phylum.split(';')
            while len(new_columns) < 3:
                new_columns.append(unassigned)
            new_columns.append(count)
            data[counter] = new_columns
            counter += 1

        num_assigned_seqs = df[column_name].count()
        num_unassigned_seqs = num_rna_seqs - num_assigned_seqs
        if num_unassigned_seqs > 0:
            data[counter] = [unassigned, unassigned, unassigned, num_unassigned_seqs]
        return data

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
        try:
            os.makedirs(self.summary_dir, exist_ok=True)
        except PermissionError:
            version_dir = os.path.join(self.study_result_dir, 'version_{}'.format(self.pipeline))
            logging.warning("Permission issue encountered on folder: {}".format(version_dir))
            os.chmod(version_dir, 0o755)
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
        f = utils.StudyDownload(_study_rootpath, file_config, self.pipeline)
        DownloadFileDatabaseHandler(self.emg_db_name).save_study_download_file(f, self.study)

    @staticmethod
    def __get_mapseq_result_file(input_file_name, result_directory, su_type, mapseq_file_extension):
        sub_dir = ''
        if su_type in ['unite', 'itsonedb']:
            sub_dir = 'its'
        res_file_re = os.path.join(result_directory, 'taxonomy-summary', sub_dir, su_type,
                                   '{}_{}{}'.format(input_file_name, su_type, mapseq_file_extension))
        if os.path.exists(res_file_re):
            return res_file_re
        else:
            logging.warning("Result file does not exist:\n{}".format(res_file_re))

    @staticmethod
    def __get_rna_fasta_file(result_directory, file_name):
        res_file_re = os.path.join(result_directory, 'sequence-categorisation', file_name)
        if os.path.exists(res_file_re):
            return res_file_re
        else:
            logging.warning("Result file does not exist:\n{}".format(res_file_re))

    @staticmethod
    def get_mapseq_result_files(analysis_result_dirs, su_type, mapseq_file_extension):
        result = []
        for input_file_name, dir in analysis_result_dirs.items():
            sub_dir = ''
            if su_type in ['unite', 'itsonedb']:
                sub_dir = 'its'
            res_file_re = os.path.join(dir, 'taxonomy-summary', sub_dir, su_type,
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

    @staticmethod
    def __build_dataframe(data):
        df = pd.DataFrame.from_dict(data, orient='index', columns=['superkingdom', 'kingdom', 'phylum', 'count'])
        return df

    @staticmethod
    def normalize_taxa_hierarchy(taxa_str):
        unassigned = 'Unassigned'
        if taxa_str.endswith('k__'):
            taxa_str = taxa_str.replace(';k__', ';{}'.format(unassigned))
        elif taxa_str.endswith('p__'):
            taxa_str = taxa_str.replace(';p__', ';{}'.format(unassigned))

        result = (lambda x: x.replace('k__;', '{};'.format(unassigned)))(taxa_str)
        result = (lambda y: y.replace('sk__', '').replace('k__', '').replace('p__', ''))(result)
        #
        while result.count(';') < 2:
            result = '{};{}'.format(result, unassigned)
        return result
