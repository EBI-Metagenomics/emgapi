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

import os
import logging
import csv
from django.core.management import BaseCommand

from emgapianns import models as m_models

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('antismash_geneclusters', action='store', type=str,
                            help='antiSMASH geneclusters csv')

    def handle(self, *args, **options):
        logger.info('CLI %r' % options)
        as_file = options['antismash_geneclusters']

        if not os.path.exists(as_file):
            logger.error('File {} does not exists'.format(as_file))
            return

        logger.info('Importing data...')
        count = 0
        with open(as_file, 'rt') as reader:
            for accession, description in csv.reader(reader, delimiter=','):
                m_models.AntiSmashGeneCluster.objects(accession=accession) \
                                             .modify(upsert=True, new=True, set__description=description)
                count += 1
        logger.info('Imported {} gene clusters.'.format(count))
