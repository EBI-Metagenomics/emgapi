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
    version = None
    result_dir = None

    def add_arguments(self, parser):
        parser.add_argument('--rootpath',
                            help="NFS root path of the results archive.",
                            default="/nfs/production/interpro/metagenomics/results/")
        parser.add_argument('result_dir', help="Result dir folder - absolute path.")
        parser.add_argument('biome', help='Lineage of GOLD biome')
        parser.add_argument('--pipeline', help='Pipeline version',
                            choices=['4.1', '5.0'], default='4.1')
        parser.add_argument('--database', help='Target emg_db_name alias', default='default')

    def handle(self, *args, **options):
        self.emg_db_name = options['database']
        self.rootpath = os.path.abspath(options['rootpath'])
        self.result_dir = os.path.abspath(options['result_dir'])
        self.biome = options['biome']
        self.version = options['pipeline']

        input_file_name = os.path.basename(self.result_dir)
        logger.info("CLI %r" % options)
        self.accession = utils.get_accession_from_result_dir_path(self.result_dir)

        metadata = self.retrieve_metadata()

        # TODO: How to sanity check AMPLICON: SSU, LSU and ITS?
        SanityCheck(self.accession, self.result_dir, metadata.experiment_type.value, self.version).check_all()

        self.call_import_study(metadata)

        self.call_import_sample(metadata)

        if isinstance(metadata, Run):
            self.call_import_run(metadata.run_accession)
        else:
            self.call_import_assembly(metadata.analysis_accession)

        analysis = self.create_or_update_analysis(metadata, input_file_name)
        self.upload_analysis_files(metadata.experiment_type.value, analysis, input_file_name)

        self.upload_statistics()

        self.populate_mongodb_taxonomy()

        if metadata.experiment_type != 'amplicon':
            self.populate_mongodb_function_and_pathways()

        logger.info("Program finished successfully.")

    def call_import_study(self, metadata):
        logger.info('Import study {}'.format(metadata.secondary_study_accession))
        study_dir = utils.get_result_dir(utils.get_study_dir(self.result_dir))
        call_command('import_study',
                     metadata.secondary_study_accession,
                     self.biome,
                     '--study_dir', study_dir)

    def call_import_sample(self, metadata):
        logger.info('Import sample {}'.format(metadata.sample_accession))
        call_command('import_sample',
                     metadata.sample_accession,
                     '--biome', self.biome)

    def call_import_run(self, run_accession):
        logger.info('Import run {}'.format(run_accession))
        call_command('import_run', run_accession, '--biome', self.biome)

    def call_import_assembly(self, analysis_accession):
        logger.info('Import assembly {}'.format(analysis_accession))
        call_command('import_assembly', analysis_accession, '--result_dir', self.result_dir, '--biome', self.biome)

    def retrieve_metadata(self):
        is_assembly = utils.is_assembly(self.accession)
        logger.info("Identified assembly accession: {0}".format(is_assembly))

        if is_assembly:
            # assembly = ena.get_assembly(assembly_name=self.accession)
            assembly = ena.get_assembly(assembly_name=self.accession,
                                        fields='secondary_study_accession,secondary_sample_accession,'
                                               'analysis_alias,analysis_accession')
            if 'sample_accession' in assembly:
                del assembly['sample_accession']
            if 'analysis_alias' in assembly:
                assembly['run_accession'] = assembly['analysis_alias']
                del assembly['analysis_alias']
            analysis = Assembly(**assembly)
        else:  # Run accession detected
            run = ena.get_run(run_accession=self.accession,
                              fields='secondary_study_accession,secondary_sample_accession,'
                                     'run_accession,library_strategy,library_source')
            if 'sample_accession' in run:
                del run['sample_accession']
            analysis = Run(**run)
        return analysis

    def get_emg_study(self, secondary_study_accession):
        return emg_models.Study.objects.using(self.emg_db_name).get(secondary_accession=secondary_study_accession)

    def get_emg_sample(self, sample_accession):
        return emg_models.Sample.objects.using(self.emg_db_name).get(accession=sample_accession)

    def get_emg_run(self, run_accession):
        return emg_models.Run.objects.using(self.emg_db_name).get(accession=run_accession)

    def get_emg_assembly(self, assembly_accession):
        return emg_models.Assembly.objects.using(self.emg_db_name).get(accession=assembly_accession)

    def get_pipeline_by_version(self):
        return emg_models.Pipeline.objects.using(self.emg_db_name).get(release_version=self.version)

    def get_analysis_status(self, description):
        return emg_models.AnalysisStatus.objects.using(self.emg_db_name).get(analysis_status=description)

    def get_experiment_type(self, experiment_typ):
        return emg_models.ExperimentType.objects.using(self.emg_db_name).get(experiment_type=experiment_typ)

    def create_or_update_analysis(self, metadata, input_file_name):
        pipeline = self.get_pipeline_by_version()
        study = self.get_emg_study(metadata.secondary_study_accession)
        sample = self.get_emg_sample(metadata.sample_accession)

        defaults = {
            'study': study,
            'sample': sample,
            'result_directory': utils.get_result_dir(self.result_dir),
            're_run_count': 0,
            'input_file_name': input_file_name,
            # Removed due to (1406, "Data too long for column 'IS_PRODUCTION_RUN' at row 1")
            # 'is_production_run': 1,
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
            run = self.get_emg_run(metadata.run_accession)
            assembly = self.get_emg_assembly(metadata.analysis_accession)
            comp_key.update({
                'external_run_ids': assembly.accession,
                'assembly': assembly,
            })
            defaults['experiment_type'] = self.get_experiment_type('assembly')
            defaults['instrument_model'] = run.instrument_model
            defaults['instrument_platform'] = run.instrument_platform
            pass
        analysis, _ = emg_models.AnalysisJob.objects.using(self.emg_db_name) \
            .update_or_create(**comp_key, defaults=defaults)
        return analysis

    def upload_analysis_files(self, experiment_type, analysis_job, input_file_name):
        dl_set = get_conf_downloadset(self.result_dir, input_file_name,
                                      self.emg_db_name, experiment_type, self.version)
        dl_set.insert_files(analysis_job)

    def upload_statistics(self):
        """
            Please note that the name of the import module is misleading as this is not just about QC stats but also
            about functional stats
        :return:
        """
        logger.info('Importing statistics...')
        call_command('import_qc', self.accession, self.rootpath, '--pipeline', self.version)

    def populate_mongodb_taxonomy(self):
        logger.info('Importing Taxonomy data...')
        call_command('import_taxonomy', self.accession, self.rootpath, '--pipeline', self.version)

    def populate_mongodb_function_and_pathways(self):
        logger.info('Importing functional and pathway data...')
        for sum_type in ['.ipr', '.go', '.go_slim', '.paths.kegg', '.pfam', '.ko', '.paths.gprops']:
            call_command('import_summary', self.accession, self.rootpath, sum_type, '--pipeline', self.version)
