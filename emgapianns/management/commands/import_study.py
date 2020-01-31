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
from emgapianns.management.lib import utils

from emgapianns.management.lib.create_or_update_study import StudyImporter

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Creates or updates a study in EMG.\n' \
           'Example call: import_study SRP101805 358 --prod_dir /home/<user>/metagenomics/results'

    def add_arguments(self, parser):
        parser.add_argument('accession',
                            help='ENAs study accession (primary or secondary accession)',
                            action='store')
        parser.add_argument('lineage',
                            help="Specify a biome which will be assigned to the study level.",
                            action='store')
        dir_locations = parser.add_mutually_exclusive_group()
        dir_locations.add_argument('--study_dir',
                                   help="NFS root path of the study in the results archive")
        dir_locations.add_argument('--rootpath',
                                   help="NFS root path of the results archive",
                                   default='/nfs/production/interpro/metagenomics/results/')
        parser.add_argument('--ena_db',
                            help="ENA's production database",
                            default='era')
        parser.add_argument('--emg_db',
                            help='Target emg_db_name alias',
                            choices=['default', 'dev', 'prod'],
                            default='default')

    def handle(self, *args, **options):
        logger.info("CLI %r" % options)

        study_accession = options['accession']
        lineage = options['lineage']
        ena_db = options['ena_db']
        emg_db = options['emg_db']

        logger.info('Importing study {}'.format(study_accession))

        study_dir = self.get_study_dir(options.get('study_dir'), options.get('rootpath'), study_accession)
        importer = StudyImporter(study_accession, study_dir, lineage, ena_db, emg_db)
        importer.run()

        logger.info("Study import finished successfully.")

    @staticmethod
    def get_study_dir(study_dir, rootpath, secondary_study_accession):
        if study_dir:
            result_dir = study_dir
        else:
            result_dir = utils.retrieve_existing_result_dir(rootpath, ['2*', '*', secondary_study_accession])

        if not result_dir:
            raise ValueError("Could not find any result directory for this study. Program will exit now!")

        return result_dir
