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
from emgapianns.management.lib.import_analysis_model import ExperimentType, identify
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

    emg_db_name = None
    biome = None
    result_dir = None

    def add_arguments(self, parser):
        parser.add_argument('accessions', help='ENA run accessions', nargs='+')
        parser.add_argument('--database', help='Target emg_db_name alias', default='default')
        parser.add_argument('--result_dir', help="Result dir folder - absolute path.")
        parser.add_argument('--biome', help='Lineage of GOLD biome')

    def handle(self, *args, **options):
        logger.info("CLI %r" % options)
        self.emg_db_name = options['database']
        self.result_dir = os.path.abspath(options['result_dir'])
        self.biome = options['biome']
        for acc in options['accessions']:
            self.import_run(acc)

        logger.info("Program finished successfully.")

    def import_run(self, accession):
        api_run_data = self.get_run_api(accession)
        db_run_data = self.get_ena_db_run(accession)
        run = self.create_or_update_run(db_run_data, api_run_data)
        self.tag_study(run, api_run_data['secondary_study_accession'])
        self.tag_sample(run, api_run_data['secondary_sample_accession'])
        library_strategy = api_run_data['library_strategy']
        library_source = api_run_data['library_source']
        self.tag_experiment_type(run, identify(library_strategy=library_strategy,
                                               library_source=library_source).value)
        run.save(using=self.emg_db_name)

    @staticmethod
    def get_run_api(accession):
        logger.info('Fetching run {} from ena api'.format(accession))
        return ena.get_run(accession)

    @staticmethod
    def get_ena_db_run(accession):
        logger.info('Fetching run {} from ena oracle DB'.format(accession))
        return ena_models.Run.objects.using('era').filter(run_id=accession).first()

    def create_or_update_run(self, db_data, api_data):
        accession = api_data['run_accession']
        logger.info('Creating run {}'.format(accession))
        status = emg_models.Status.objects.using(self.emg_db_name).get(status_id=db_data.status_id)
        defaults = utils.sanitise_fields({
            'instrument_platform': api_data['instrument_platform'],
            'instrument_model': api_data['instrument_model'],
            'status': status,
            'secondary_accession': accession
        })
        run, created = emg_models.Run.objects.using(self.emg_db_name).update_or_create(
            accession=accession,
            defaults=defaults
        )
        return run

    @staticmethod
    def get_ena_sample(sample_accession):
        return ena.get_sample(sample_accession=sample_accession)

    @staticmethod
    def get_run_studies(sample):
        return ena.get_sample_studies(sample.primary_accession)

    def tag_study(self, run, study_accession):
        try:
            run.study = emg_models.Study.objects.using(self.emg_db_name) \
                .get(secondary_accession=study_accession)
        except emg_models.Study.DoesNotExist:
            logging.warning('Study {} does not exist in emg DB'.format(study_accession))
            logging.info("Importing study {} now...".format(study_accession))
            study_dir = utils.get_result_dir(utils.get_study_dir(self.result_dir))
            call_command('import_study',
                         study_accession,
                         self.biome,
                         '--study_dir', study_dir)
            try:
                run.study = emg_models.Study.objects.using(self.emg_db_name) \
                    .get(secondary_accession=study_accession)
            except emg_models.Study.DoesNotExist:
                raise emg_models.Study.DoesNotExist('Study {} does not exist in emg DB'.format(study_accession))

    def tag_sample(self, run, sample_accession):
        try:
            run.sample = emg_models.Sample.objects.using(self.emg_db_name) \
                .get(accession=sample_accession)
        except emg_models.Sample.DoesNotExist:
            raise emg_models.Sample.DoesNotExist('Sample {} does not exist in emg DB'.format(sample_accession))

    def tag_experiment_type(self, run, experiment_type):
        try:
            run.experiment_type = emg_models.ExperimentType.objects.using(self.emg_db_name) \
                .get(experiment_type=experiment_type.lower())
        except emg_models.ExperimentType.DoesNotExist:
            raise emg_models.ExperimentType \
                .DoesNotExist('Experiment type {} does not exist in database'.format(experiment_type))
