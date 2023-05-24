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
import sys

from django.db import IntegrityError
from django.db.models import Q
from django.utils import timezone
from django.core.management import BaseCommand

from emgapianns.management.lib.utils import get_lat_long, sanitise_fields

from ena_portal_api import ena_handler

from emgapi import models as emg_models
from emgena import models as ena_models

logger = logging.getLogger(__name__)

ena = ena_handler.EnaApiHandler()


class Command(BaseCommand):
    help = 'Imports new objects into EMG.'

    obj_list = list()
    rootpath = None
    genome_folders = None

    emg_db = None
    ena_db = None
    biome = None

    def add_arguments(self, parser):
        parser.add_argument('accessions', help='ENA sample accessions', nargs='+')
        parser.add_argument('--ena_db',
                            help="ENA's production database",
                            default='era')
        parser.add_argument('--emg_db',
                            help='Target emg_db_name alias',
                            choices=['default', 'dev', 'prod'],
                            default='default')
        parser.add_argument('--biome', help='Lineage of GOLD biome')

    def handle(self, *args, **options):
        logger.info("CLI %r" % options)
        self.emg_db = options['emg_db']
        self.ena_db = options['ena_db']
        self.biome = options['biome']

        for acc in options['accessions']:
            logger.info('Importing sample {}'.format(acc))
            self.import_sample(acc)
            logger.info("Sample import finished successfully.")

    def import_sample(self, accession):
        ena_db_model = self.get_ena_db_sample(accession)
        api_sample_data = self.fetch_sample_api(accession)
        sample = self.create_or_update_sample(ena_db_model, api_sample_data)
        self.tag_sample_anns(sample, api_sample_data)
        self.tag_study(sample)

    @staticmethod
    def fetch_sample_api(accession):
        logger.info('Fetching sample {} from ena api'.format(accession))
        return ena.get_sample(accession)

    def create_or_update_sample(self, ena_db_model, api_data):
        accession = api_data['secondary_sample_accession']
        logger.debug('Getting the biome from the DB.')
        try:
            biome_model = emg_models.Biome.objects.using(self.emg_db).get(lineage=self.biome)
        except emg_models.Biome.DoesNotExist as exception:
            logger.exception(exception)
            logger.error(f'The supplied biome is not valid. Biome: "{self.biome}"')
            # TODO: replace with raise CommandError
            sys.exit(1)

        logger.info('Creating sample {}'.format(accession))

        defaults = sanitise_fields({
            'collection_date': api_data['collection_date'],
            'is_private': api_data.get('status', "private").strip().lower() == "private",
            'sample_desc': api_data['description'],
            'environment_biome': api_data['environment_biome'],
            'environment_feature': api_data['environment_feature'],
            'environment_material': api_data['environment_material'],
            'sample_name': api_data['sample_alias'],
            'sample_alias': api_data['sample_alias'],
            'host_tax_id': self.__get_host_tax_id(api_data['host_tax_id']),
            'species': self.__get_species(),
            'biome': biome_model,
            'last_update': timezone.now(),
            'submission_account_id': ena_db_model.submission_account_id,
        })

        if api_data.get('location'):
            defaults['latitude'], defaults['longitude'] = get_lat_long(api_data['location'])

        # defensive mechanism - portal API v2.0 migration
        # this should not happend here, but the portal API will return:
        # 
        # accession	sample_accession
        # FX526847	SAMD00010145;SAMD00010147
        # if there is more than one sample linked to a record
        # again, this should not happend here, but just in case

        assert ";" not in api_data['sample_accession']

        sample, created = emg_models.Sample.objects.using(self.emg_db).update_or_create(
            accession=accession,
            primary_accession=api_data['sample_accession'],
            defaults=defaults
        )
        return sample

    def tag_sample_anns(self, sample, sample_data):
        logger.info('Tagging annotations for sample {}'.format(sample.accession))
        if sample_data.get('location'):
            lat, lng = get_lat_long(sample_data['location'])
            self.create_sample_ann(sample, 'geographic location (latitude)', lat)
            self.create_sample_ann(sample, 'geographic location (longitude)', lng)

        simple_mappings = (
            ('collection date', 'collection_date'),
            ('ENA checklist', 'checklist'),
            ('geographic location (country and/or sea,region)', 'country'),
            ('environment (feature)', 'environment_feature'),
            ('environment (biome)', 'environment_biome'),
            ('environment (material)', 'environment_material'),
            ('environmental package', 'ncbi_reporting_standard'),
            ('sequencing method', 'sequencing_method'),
            ('host taxid', 'host_tax_id'),
            ('host sex', 'host_sex'),
            ('body site', 'host_body_site'),
            ('gravidity', 'host_gravidity'),
            ('host genotype', 'host_genotype'),
            ('host phenotype', 'host_phenotype'),
            ('host growth conditions', 'host_growth_conditions'),
            ('depth', 'depth'),
            ('altitude', 'altitude'),
            ('elevation', 'elevation'),
            ('investigation type', 'investigation_type'),
            ('experimental factor', 'experimental_factor'),
            ('temperature', 'temperature'),
            ('salinity', 'salinity'),
            ('project name', 'project_name'),
            ('target gene', 'target_gene'),
            ('host scientific name', 'host')
        )

        for var_name, api_field in simple_mappings:
            self.tag_sample_ann(sample, sample_data, var_name, api_field)

    def tag_sample_ann(self, sample, sample_data, var_name, data_key):
        if sample_data.get(data_key):
            self.create_sample_ann(sample, var_name, sample_data[data_key])

    def create_sample_ann(self, sample, var_name, value, unit=None):
        var = self.get_variable(var_name)
        defaults = {
            'var_val_ucv': value,
            'units': unit
        }
        emg_models.SampleAnn.objects.using(self.emg_db) \
            .update_or_create(sample=sample, var=var, defaults=defaults)

    def get_ena_db_sample(self, accession):
        logger.info('Fetching sample {} from ena oracle DB'.format(accession))
        return ena_models.Sample.objects.using(self.ena_db).filter(Q(sample_id=accession) | Q(biosample_id=accession))[0]

    def get_variable(self, name):
        try:
            return emg_models.VariableNames.objects.using(self.emg_db).get(var_name=name)
        except emg_models.VariableNames.DoesNotExist:
            raise emg_models.VariableNames.DoesNotExist('Variable name {} is missing in db'.format(name))

    @staticmethod
    def get_sample_studies(sample):
        try:
            return ena.get_sample_studies(sample.primary_accession)
        except ValueError:
            return ena.get_sample_studies(primary_sample_accession=sample.primary_accession, result="analysis")

    def tag_study(self, sample):
        study_accessions = self.get_sample_studies(sample)
        studies = emg_models.Study.objects.using(self.emg_db).filter(secondary_accession__in=study_accessions)
        for study in studies:
            try:
                emg_models.StudySample(study=study, sample=sample).save(using=self.emg_db)
            except IntegrityError:
                pass
        if not len(studies):
            logger.warning('No studies tagged to sample {}'.format(sample.accession))

    def __get_host_tax_id(self, ena_host_tax_id):
        if self.biome.startswith('root:Host-associated:Human'):
            return 9606
        else:
            return ena_host_tax_id

    def __get_species(self):
        if self.biome.startswith('root:Host-associated:Human'):
            return 'Homo sapiens'
        else:
            return None
