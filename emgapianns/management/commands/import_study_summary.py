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
from django.core.management import BaseCommand
from ena_portal_api import ena_handler
from emgapianns.management.lib.study_summary_generator import StudySummaryGenerator

logger = logging.getLogger(__name__)

cog_cache = {}
ipr_cache = {}
kegg_cache = {}

ena = ena_handler.EnaApiHandler()


class Command(BaseCommand):
    help = 'Generates project summary files (for taxonomy (SSU, LSU), GO and InterProScan annotations)'

    obj_list = list()
    rootpath = None

    emg_db_name = None
    biome = None
    study_accession = None
    summary_dir = None
    study = None
    pipeline = None
    study_result_dir = None

    def add_arguments(self, parser):
        parser.add_argument('accession', help="Specify a secondary study accession.")
        parser.add_argument('pipeline', help='Pipeline version',
                            choices=['4.1', '5.0'], default='4.1')
        parser.add_argument('--rootpath',
                            help="NFS root path of the results archive.",
                            default="/nfs/production/interpro/metagenomics/results/")
        parser.add_argument('--nfs-public-rootpath',
                            help="NFS public root path of the results archive.",
                            default="/nfs/public/ro/metagenomics/results/")
        parser.add_argument('--database',
                            help='Target emg_db_name alias',
                            choices=['default', 'dev', 'prod'],
                            default='default')
        parser.set_defaults(no_study_summary=False)
        parser.add_argument('-v', '--verbose', action='store_true')

    def handle(self, *args, **options):
        logger.info('CLI %r' % options)
        logging.basicConfig(level=logging.DEBUG if options['verbose'] else logging.INFO)
        study_accession = options['accession']
        pipeline = options['pipeline']
        database = options['database']
        rootpath = os.path.abspath(options['rootpath'])
        nfs_public_rootpath = os.path.abspath(options['nfs_public_rootpath'])

        gen = StudySummaryGenerator(study_accession, pipeline, rootpath, nfs_public_rootpath, database)
        gen.run()
