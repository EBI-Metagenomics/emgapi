#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 EMBL - European Bioinformatics Institute
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
import logging
import os
from pathlib import Path
from django.core.management import BaseCommand
from ena_portal_api import ena_handler
import pandas as pd
import numpy as np
from emgapianns.management.lib import utils
from emgapi import models as emg_models

logger = logging.getLogger(__name__)

cog_cache = {}
ipr_cache = {}
kegg_cache = {}

ena = ena_handler.EnaApiHandler()


class Command(BaseCommand):
    help = 'Generate new '

    obj_list = list()
    rootpath = None

    emg_db_name = None
    biome = None
    study_accession = None
    summary_dir = None
    study = None
    pipeline = None

    def add_arguments(self, parser):
        parser.add_argument('rootpath',
                            help='NFS root path of the study archive, eg /..../ERP001736/version_4.1/')
        parser.add_argument('--database', help='Target emg_db_name alias', default='default')

    def handle(self, *args, **options):
        self.emg_db_name = options['database']
        self.rootpath = os.path.abspath(options['rootpath'])
        self.study_accession = utils.get_study_accession_from_rootpath(self.rootpath)
        self.study = emg_models.Study.objects.using(self.emg_db_name).get(secondary_accession=self.study_accession)

        pipeline_version = utils.get_pipeline_version(self.rootpath)
        self.pipeline = emg_models.Pipeline.objects.using(self.emg_db_name).get(release_version=pipeline_version)

        self.summary_dir = utils.get_study_summary_dir(self.rootpath)
        self.create_summary_dir()

        logger.info('CLI %r' % options)

        self.generate_taxonomy_phylum_summary('SSU', 'phylum_taxonomy_abundances_SSU_v4.1.tsv')
        self.generate_taxonomy_phylum_summary('LSU', 'phylum_taxonomy_abundances_LSU_v4.1.tsv')

        self.generate_taxonomy_summary('SSU', 'taxonomy_abundances_SSU_v4.1.tsv')
        self.generate_taxonomy_summary('LSU', 'taxonomy_abundances_LSU_v4.1.tsv')

        self.generate_ipr_summary('IPR_abundances_v4.1.tsv')

        self.generate_go_summary('slim')
        self.generate_go_summary('full')

        # TODO handle diversity script

    def generate_taxonomy_phylum_summary(self, su_type, filename):
        res_file_re = os.path.join('**', 'taxonomy-summary', su_type, 'kingdom-counts.txt')
        res_files = self.get_raw_result_files(res_file_re)
        study_df = self.merge_dfs(res_files,
                                  delimiter='\t',
                                  key=['kingdom', 'phylum'],
                                  raw_cols=['kingdom', 'phylum', 'count', 'ignored'])
        self.write_results_file(study_df, filename)

        alias = '{}_phylum_taxonomy_abundances_{}_v4.1.tsv'.format(self.study_accession, su_type)
        description = 'Phylum level taxonomies {}'.format(su_type)
        group = 'Taxonomic analysis {} rRNA'.format(su_type)
        self.upload_study_file(filename, alias, description, group)

    def generate_taxonomy_summary(self, su_type, filename):
        res_file_re = os.path.join('**', 'taxonomy-summary', su_type, '*{}*.fasta.mseq.tsv'.format(su_type))
        res_files = self.get_raw_result_files(res_file_re)
        study_df = self.merge_dfs(res_files,
                                  key=['lineage'],
                                  delimiter='\t',
                                  raw_cols=['OTU', 'count', 'lineage'],
                                  skip_rows=2)
        study_df = study_df.rename(columns={'lineage': '#SampleID'})
        self.write_results_file(study_df, filename)

        alias = '{}_taxonomy_abundances_{}_v4.1.tsv'.format(self.study_accession, su_type)
        description = 'Taxonomic assignments {}'.format(su_type)
        group = 'Taxonomic analysis {} rRNA'.format(su_type)
        self.upload_study_file(filename, alias, description, group)

    def get_raw_result_files(self, res_file_re):
        paths = list(Path(self.rootpath).glob(res_file_re))
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

    def generate_ipr_summary(self, filename):
        res_file_re = os.path.join('**', '*_summary.ipr')
        res_files = self.get_raw_result_files(res_file_re)
        study_df = self.merge_dfs(res_files, delimiter=',',
                                  key=['IPR', 'description'],
                                  raw_cols=['IPR', 'description', 'count'])
        self.write_results_file(study_df, filename)

        alias = '{}_IPR_abundances_v4.1.tsv'.format(self.study_accession)
        description = 'InterPro matches'
        self.upload_study_file(filename, alias, description, 'Functional analysis')

    def generate_go_summary(self, mode):
        if mode == 'slim':
            raw_file_re = '*.go_slim'
            sum_file = 'GO-slim'
            description = 'GO slim annotation'
        else:
            raw_file_re = '*.go'
            sum_file = 'GO'
            description = 'Complete GO annotation'
        res_file_re = os.path.join('**', raw_file_re)
        res_files = self.get_raw_result_files(res_file_re)
        study_df = self.merge_dfs(res_files, delimiter=',',
                                  key=['GO', 'description', 'category'],
                                  raw_cols=['GO', 'description', 'category', 'count'])
        study_df['description'] = study_df['description'].str.replace(',', '@')
        study_df['category'] = study_df['category'].str.replace('_', ' ')
        realname = sum_file + '_abundances_v4.1.tsv'
        self.write_results_file(study_df, realname)

        self.generate_filtered_go_summary(study_df,
                                          'category == "cellular component"',
                                          'CC_{}_abundances_v4.1.tsv'.format(sum_file))

        self.generate_filtered_go_summary(study_df,
                                          'category == "biological process"',
                                          'BP_{}_abundances_v4.1.tsv'.format(sum_file))

        self.generate_filtered_go_summary(study_df,
                                          'category not in ["biological process", "cellular component"]',
                                          'MF_{}_abundances_v4.1.tsv'.format(sum_file))

        alias = '{}_{}_abundances_v4.1.tsv'.format(self.study_accession, sum_file)
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
            'subdir': 'version_4.1/project-summary',
            '_required': True
        }
        utils.StudyDownload(self.emg_db_name, self.rootpath, file_config, self.pipeline).save(self.study)
