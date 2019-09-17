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
import getpass

from django.core.management import BaseCommand, call_command
from django.utils import timezone
from ena_portal_api import ena_handler

from emgapianns.management.lib import utils
from emgapianns.management.lib.sanity_check import SanityCheck
from emgapianns.management.lib.import_analysis_model import Assembly, Run
from emgapianns.management.lib.utils import get_conf_downloadset

from emgapi import models as emg_models

logger = logging.getLogger(__name__)

cog_cache = {}
ipr_cache = {}
kegg_cache = {}

ena = ena_handler.EnaApiHandler()

"""
    Cl call:
        emgcli import_analysis <primary_accession> /home/maxim/
    Draft
    Inputs:
        - Path to the result directory
"""


class Command(BaseCommand):
    help = 'Imports new objects into EMG.'

    obj_list = list()
    rootpath = None

    emg_db_name = None
    biome = None
    accession = None

    def add_arguments(self, parser):
        parser.add_argument('rootpath',
                            help="NFS root path of the results archive")
        parser.add_argument('biome', help='Lineage of GOLD biome')

        parser.add_argument('--database', help='Target emg_db_name alias', default='default')

    def handle(self, *args, **options):
        self.emg_db_name = options['database']
        self.rootpath = os.path.abspath(options['rootpath'])
        self.biome = options['biome']

        input_file_name = os.path.basename(self.rootpath)
        logger.info("CLI %r" % options)
        self.accession = utils.get_accession_from_rootpath(self.rootpath)

        metadata = self.retrieve_metadata()

        SanityCheck(self.accession, self.rootpath, metadata.experiment_type).check_all()

        self.call_import_study(metadata)

        self.call_import_sample(metadata)

        if isinstance(metadata, Run):
            self.call_import_run(metadata.run_accession)
        else:
            self.call_import_assembly(metadata.analysis_accession)

        analysis = self.create_or_update_analysis(metadata, input_file_name)
        self.upload_analysis_files(metadata.experiment_type, analysis, input_file_name)

        self.upload_analysis_data()

        logger.info("Program finished successfully.")

    def call_import_study(self, metadata):
        logger.info('Import study {}'.format(metadata.secondary_study_accession))
        study_dir = utils.get_study_dir(self.rootpath)
        call_command('import_study',
                     metadata.secondary_study_accession,
                     self.biome,
                     '--study_dir', study_dir)

    def call_import_sample(self, metadata):
        logger.info('Import sample {}'.format(metadata.sample_accession))
        call_command('import_sample',
                     metadata.sample_accession,
                     '--biome', self.biome)

    @staticmethod
    def call_import_run(run_accession):
        logger.info('Import run {}'.format(run_accession))
        call_command('import_run', run_accession)

    @staticmethod
    def call_import_assembly(analysis_accession):
        logger.info('Import assembly {}'.format(analysis_accession))
        call_command('import_assembly', analysis_accession)

    def retrieve_metadata(self):
        is_assembly = utils.is_assembly(self.accession)
        logger.info("Identified assembly accession: {0}".format(is_assembly))

        if is_assembly:
            analysis = Assembly(**ena.get_assembly(assembly_name=self.accession))
        else:  # Run accession detected
            analysis = Run(**ena.get_run(run_accession=self.accession,
                                         fields='secondary_study_accession,secondary_sample_accession,'
                                                'run_accession,library_strategy'))
        return analysis

    def get_emg_study(self, secondary_study_accession):
        return emg_models.Study.objects.using(self.emg_db_name).get(secondary_accession=secondary_study_accession)

    def get_emg_sample(self, sample_accession):
        return emg_models.Sample.objects.using(self.emg_db_name).get(accession=sample_accession)

    def get_emg_run(self, run_accession):
        return emg_models.Run.objects.using(self.emg_db_name).get(accession=run_accession)

    def get_emg_assembly(self, assembly_accession):
        return emg_models.Assembly.objects.using(self.emg_db_name).get(analysis_accession=assembly_accession)

    def get_pipeline_version(self):
        return emg_models.Pipeline.objects.using(self.emg_db_name).order_by('-release_date').first()

    def get_analysis_status(self, description):
        return emg_models.AnalysisStatus.objects.using(self.emg_db_name).get(analysis_status=description)

    def create_or_update_analysis(self, metadata, input_file_name):
        pipeline = self.get_pipeline_version()
        study = self.get_emg_study(metadata.secondary_study_accession)
        sample = self.get_emg_sample(metadata.sample_accession)

        defaults = {
            'study': study,
            'sample': sample,
            'result_directory': self.rootpath,
            're_run_count': 0,
            'input_file_name': input_file_name,
            'is_production_run': 1,
            'analysis_status': self.get_analysis_status('completed'),
            'submit_time': timezone.now(),
            'complete_time': timezone.now(),
            'job_operator': getpass.getuser()
        }
        comp_key = {
            'pipeline': pipeline
        }

        if isinstance(metadata, Run):
            run = self.get_emg_run(metadata.run_accession)
            comp_key.update({
                'external_run_ids': run.accession,
                'run': run,
                'secondary_accession': run.accession
            })
            defaults['instrument_model'] = run.instrument_model
            defaults['instrument_platform'] = run.instrument_platform
            defaults['experiment_type'] = run.experiment_type
            defaults['run_status_id'] = run.status_id
        else:
            assembly = self.get_emg_assembly(metadata.analysis_accession)
            comp_key.update({
                'external_run_ids': assembly.analysis_accession,
                'assembly': assembly
            })
            pass
        analysis, _ = emg_models.AnalysisJob.objects.using(self.emg_db_name).update_or_create(**comp_key,
                                                                                              defaults=defaults)
        return analysis

    def upload_analysis_files(self, experiment_type, analysis_job, input_file_name):
        dl_set = get_conf_downloadset(self.rootpath, input_file_name, self.emg_db_name, experiment_type)
        dl_set.insert_files(analysis_job)

    def upload_analysis_data(self):
        results_dir = utils.retrieve_existing_result_dir(self.rootpath, self.accession)
        logger.info('Importing QC stats')
        call_command('import_qc', self.accession, results_dir)
        logger.info('Importing Taxonomy stats')
        call_command('import_taxonomy', self.accession, results_dir)
        for sum_type in ['.ipr', '.go', '.go_slim']:
            call_command('import_summary', self.accession, results_dir, sum_type)
