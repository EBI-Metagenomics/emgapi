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

from django.core.management import BaseCommand, call_command
from emgapianns.management.lib.utils import sanitise_fields, is_run_accession
from ena_portal_api import ena_handler
from emgapi import models as emg_models
from emgena import models as ena_models

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

    def add_arguments(self, parser):
        parser.add_argument('accessions', help='ENA assembly accessions', nargs='+')
        parser.add_argument('--database', help='Target emg_db_name alias', default='default')

    def handle(self, *args, **options):
        logger.info("CLI %r" % options)
        self.emg_db_name = options['database']
        for acc in options['accessions']:
            self.import_assembly(acc)

        logger.info("Program finished successfully.")

    def import_assembly(self, accession):
        db_assembly_data = self.get_ena_db_assembly(accession)
        assembly = self.create_or_update_assembly(db_assembly_data)
        self.tag_study(assembly, db_assembly_data.primary_study_accession)
        self.tag_sample(assembly, db_assembly_data.sample_id)
        self.tag_experiment_type(assembly, 'assembly')
        self.tag_optional_run(assembly, db_assembly_data.name)

        assembly.save(using=self.emg_db_name)

    @staticmethod
    def get_ena_db_assembly(accession):
        logger.info('Fetching assembly {} from ena oracle DB'.format(accession))
        return ena_models.Assembly.objects.using('ena').filter(assembly_id=accession).first()

    def create_or_update_assembly(self, era_db_data):
        accession = era_db_data.assembly_id

        logger.info('Creating assembly {}'.format(accession))
        status = emg_models.Status.objects.using(self.emg_db_name).get(status_id=era_db_data.status_id)
        defaults = sanitise_fields({
            'status_id': status,
            'wgs_accession': era_db_data.wgs_accession,
            'legacy_accession': era_db_data.gc_id,
        })
        assembly, created = emg_models.Assembly.objects.using(self.emg_db_name).update_or_create(
            accession=accession,
            defaults=defaults
        )
        return assembly

    @staticmethod
    def get_ena_sample(sample_accession):
        return ena.get_sample(sample_accession=sample_accession)

    @staticmethod
    def get_assembly_studies(sample):
        return ena.get_sample_studies(sample.primary_accession)

    def tag_study(self, assembly, study_accession):
        try:
            assembly.study = emg_models.Study.objects.using(self.emg_db_name) \
                .get(project_id=study_accession)
        except emg_models.Study.DoesNotExist:
            raise emg_models.Study.DoesNotExist('Study {} does not exist in emg DB'.format(study_accession))

    def tag_sample(self, assembly, sample_accession):
        try:
            sample = emg_models.Sample.objects.using(self.emg_db_name) \
                .get(accession=sample_accession)
            emg_models.AssemblySample.objects.using(self.emg_db_name).get_or_create(assembly=assembly, sample=sample)
        except emg_models.Sample.DoesNotExist:
            raise emg_models.Sample.DoesNotExist('Sample {} does not exist in emg DB'.format(sample_accession))

    def tag_experiment_type(self, assembly, experiment_type):
        try:
            assembly.experiment_type = emg_models.ExperimentType.objects.using(self.emg_db_name) \
                .get(experiment_type=experiment_type.lower())
        except emg_models.ExperimentType.DoesNotExist:
            raise emg_models.ExperimentType \
                .DoesNotExist('Experiment type {} does not exist in database'.format(experiment_type))

    def tag_optional_run(self, assembly, name):
        if is_run_accession(name):
            self.tag_run(assembly, name)

    def tag_run(self, assembly, run_accession):
        try:
            call_command('import_run', run_accession)
            run = emg_models.Run.objects.using(self.emg_db_name) \
                .get(accession=run_accession)
            emg_models.AssemblyRun.objects.using(self.emg_db_name).get_or_create(assembly=assembly, run=run)
        except emg_models.Run.DoesNotExist:
            raise emg_models.Run \
                .DoesNotExist('Run {} does not exist in database'.format(run_accession))
