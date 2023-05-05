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

from django.core.management import BaseCommand, call_command
from emgapi import models as emg_models
from emgapianns.management.lib import utils
from emgapianns.management.lib.import_analysis_model import identify
from emgena import models as ena_models
from ena_portal_api import ena_handler

logger = logging.getLogger(__name__)

cog_cache = {}
ipr_cache = {}
kegg_cache = {}

ena = ena_handler.EnaApiHandler()


class Command(BaseCommand):
    help = 'Imports new objects into EMG.'

    obj_list = list()
    rootpath = None
    genome_folders = None

    emg_db = None
    biome = None
    result_dir = None
    library_strategy = None

    def add_arguments(self, parser):
        parser.add_argument('accessions', help='ENA run accessions', nargs='+')
        parser.add_argument('--emg_db',
                            help='Target emg_db_name alias',
                            choices=['default', 'dev', 'prod'],
                            default='default')
        parser.add_argument('--result_dir', help="Result dir folder - absolute path.")
        parser.add_argument('--biome', help='Lineage of GOLD biome')
        parser.add_argument('--import-study', help="Import the Study if ti does not exist", action="store_true")
        parser.add_argument('--library_strategy', help='Library strategy',
                            choices=['AMPLICON', 'WGS', 'ASSEMBLY', 'RNA-Seq', 'WGA'])

    def handle(self, *args, **options):
        logger.info("CLI %r" % options)
        self.emg_db = options['emg_db']
        self.import_study = options['import_study']
        if options['result_dir']:
            self.result_dir = os.path.abspath(options['result_dir'])
        if options['biome']:
            self.biome = options['biome']
        if options['library_strategy']:
            self.library_strategy = options['library_strategy']
        for acc in options['accessions']:
            logger.info('Importing run {}'.format(acc))
            self.import_run(acc)
            logger.info("Run import finished successfully.")

    def import_run(self, accession):
        api_run_data = self.get_run_api(accession)
        run = self.create_or_update_run(api_run_data)
        
        if self.library_strategy:
            _library_strategy = self.library_strategy
        else:
            _library_strategy = api_run_data['library_strategy']
        _library_source = api_run_data['library_source']
        self.tag_experiment_type(run, identify(library_strategy=_library_strategy,
                                               library_source=_library_source).value)

        self.tag_study(run, api_run_data['secondary_study_accession'], get_or_create=self.import_study)

        # The portal API v2.0 squeezes the samples data into a single row, if there many
        # samples associated with an entity
        sample_accessions = api_run_data.get('secondary_sample_accession')
        if sample_accessions:
            for sample_accession in sample_accessions.split(';'):
                self.tag_sample(run, sample_accession.strip())

        # Validate and save #
        run.full_clean()
        run.save(using=self.emg_db)

    @staticmethod
    def get_run_api(accession):
        logger.info('Fetching run {} from ena api'.format(accession))
        return ena.get_run(accession)

    def create_or_update_run(self, api_data):
        accession = api_data['run_accession']
        logger.info(f'Creating run {accession}')
        defaults = utils.sanitise_fields({
            'instrument_platform': api_data['instrument_platform'],
            'instrument_model': api_data['instrument_model'],
            'is_private': int(api_data["status_id"]) == 2,
            'secondary_accession': accession
        })
        run, created = emg_models.Run.objects.using(self.emg_db).update_or_create(
            accession=accession,
            defaults=defaults
        )
        return run

    def tag_study(self, run, study_accession, get_or_create=False):
        """Link the Run to the Study.
        If `get_or_create` is True the code will run import_study, in case the Study doesn't exist.
        If get_or_create is False and the Study doesn't exist, the run field ena_study_accession
        will be populated with the value study_accesion.
        """
        try:
            run.study = emg_models.Study.objects.using(self.emg_db) \
                .get(secondary_accession=study_accession)
        except emg_models.Study.DoesNotExist:
            logging.warning("Study {study_accession} does not exist in emg DB")

            if not get_or_create:
                logging.warning("Skipping the study import")
                logging.info("Storing the study accession {study_accession} in the run ena_study_accession field")
                run.ena_study_accession = study_accession
                return 

            logging.info("Importing study {} now...".format(study_accession))
            if self.result_dir:
                study_dir = utils.get_result_dir(utils.get_study_dir(self.result_dir))
                call_command('import_study', study_accession, self.biome, '--study_dir', study_dir)
            else:
                call_command('import_study', study_accession, self.biome)
            try:
                run.study = emg_models.Study.objects.using(self.emg_db) \
                    .get(secondary_accession=study_accession)
            except emg_models.Study.DoesNotExist:
                raise emg_models.Study.DoesNotExist('Study {} does not exist in emg DB'.format(study_accession))

    def tag_sample(self, run, sample_accession):
        try:
            run.sample = emg_models.Sample.objects.using(self.emg_db) \
                .get(accession=sample_accession)
        except emg_models.Sample.DoesNotExist:
            raise emg_models.Sample.DoesNotExist('Sample {} does not exist in emg DB'.format(sample_accession))

    def tag_experiment_type(self, run, experiment_type):
        try:
            run.experiment_type = emg_models.ExperimentType.objects.using(self.emg_db) \
                .get(experiment_type=experiment_type.lower())
        except emg_models.ExperimentType.DoesNotExist:
            raise emg_models.ExperimentType \
                .DoesNotExist('Experiment type {} does not exist in database'.format(experiment_type))
