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

from django.core.management import BaseCommand

from emgapianns.management.lib.create_or_update_study import run_create_or_update_study

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Creates or updates a study in EMG.'

    # Example call: import_study SRP101805 358 --prod_dir /home/<user>/metagenomics/results

    def add_arguments(self, parser):
        parser.add_argument('accession',
                            help='ENAs study accession (primary or secondary accession)',
                            type=str,
                            action='store')
        parser.add_argument('biome-id',
                            help="Specify a biome which will be assigned to the study level.",
                            type=int,
                            action='store')
        parser.add_argument('--prod_dir',
                            help="NFS root path of the results archive",
                            default='/nfs/production/interpro/metagenomics/results/')
        parser.add_argument('--ena_db',
                            help="ENA's production database",
                            default='era_pro')

    def handle(self, *args, **options):
        logger.info("CLI %r" % options)

        secondary_study_accession = options['accession']
        rootpath = options.get('prod_dir')
        biome_id = options['biome-id']
        database = options['ena_db']

        run_create_or_update_study(secondary_study_accession, rootpath, biome_id, database)

        logger.info("Program finished successfully.")
