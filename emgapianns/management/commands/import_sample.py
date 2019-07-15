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

from django.utils import timezone
from django.core.management import BaseCommand
from emgapianns.management.lib.utils import get_lat_long
from ena_portal_api import ena_handler
from emgapi import models as emg_models

logger = logging.getLogger(__name__)

cog_cache = {}
ipr_cache = {}
kegg_cache = {}

ena = ena_handler.EnaApiHandler()


def sanitise_sample_fields(data):
    # Remove blank fields
    keys = list(data.keys())
    for k in keys:
        if type(data[k]) == str and len(data[k]) == 0:
            del data[k]

    return data


class Command(BaseCommand):
    help = 'Imports new objects into EMG.'

    obj_list = list()
    rootpath = None
    genome_folders = None

    database = None
    is_private_data = None
    biome = None

    def add_arguments(self, parser):
        parser.add_argument('accessions', help='ENA sample accessions', nargs='+')
        parser.add_argument('--database', help='Target database alias', default='default')
        parser.add_argument('--private', help='Set privacy status', action='store_true')
        parser.add_argument('--biome', help='GOLD biome of samples')

    def handle(self, *args, **options):
        logger.info("CLI %r" % options)
        self.database = options['database']
        self.is_private_data = options['private']
        self.biome = options['biome']
        for acc in options['accessions']:
            self.import_sample(acc)

        logger.info("Program finished successfully.")

    def import_sample(self, accession):
        sample_data = ena.get_sample(accession)
        print(sample_data)
        sample = self.create_or_update_sample(sample_data)
        self.tag_sample_anns(sample, sample_data)

    def create_or_update_sample(self, data):
        defaults = sanitise_sample_fields({
            'collection_date': data['collection_date'],
            'is_public': not self.is_private_data,
            'sample_desc': data['description'],
            'environment_biome': data['environment_biome'],
            'environment_feature': data['environment_feature'],
            'environment_material': data['environment_material'],
            'sample_name': data['sample_alias'],
            'sample_alias': data['sample_alias'],
            'host_tax_id': data['host_tax_id'],
            'species': '',  # TODO
            'biome': self.get_biome(self.biome),
            'last_update': timezone.now()
        })

        sample, created = emg_models.Sample.objects.using(self.database).update_or_create(
            accession=data['secondary_sample_accession'],
            primary_accession=data['sample_accession'],
            defaults=defaults
        )
        return sample

    def tag_sample_anns(self, sample, sample_data):
        if sample_data.get('checklist'):
            self.create_sample_ann(sample, 'ENA checklist', sample_data['checklist'])
        if sample_data.get('location'):
            lat, lng = get_lat_long(sample_data['location'])
            self.create_sample_ann(sample, 'geographic location (latitude)', lat)
            self.create_sample_ann(sample, 'geographic location (longitude)', lng)
        if sample_data.get('country'):
            self.create_sample_ann(sample, 'geographic location (country and/or sea,region)', sample_data['country'])

    def create_sample_ann(self, sample, var_name, value, unit=None):
        var = self.get_variable(var_name)
        defaults = {
            'var_val_ucv': value,
            'units': unit
        }
        emg_models.SampleAnn.objects.using(self.database).update_or_create(sample=sample, var=var, defaults=defaults)

    def get_biome(self, lineage):
        return emg_models.Biome.objects.using(self.database).get(lineage=lineage)

    def get_variable(self, name):
        return emg_models.VariableNames.objects.using(self.database).get(var_name=name)

    def tag_study(self, sample_data):
        print(ena.get_sample_studies(sample_data['sample_accession']))
