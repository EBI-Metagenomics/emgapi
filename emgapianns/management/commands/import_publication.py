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

from emgapianns.management.lib.europe_pmc_api.europe_pmc_api_handler import EuropePMCApiHandler

logger = logging.getLogger(__name__)


def lookup_publication_by_pubmed_id(pubmed_id):
    api_handler = EuropePMCApiHandler()
    return api_handler.get_publication_by_pubmed_id(pubmed_id)


def lookup_publication_by_project_id(project_id):
    # TODO: Implement
    pass


class Command(BaseCommand):
    help = 'Creates or updates a publication in EMG.'

    def add_arguments(self, parser):
        # TODO: Consider lookup by project id
        parser.add_argument('pubmed-id',
                            help='PubMed identifier (PMID)',
                            type=str,
                            action='store')

    def handle(self, *args, **options):
        logger.info("CLI %r" % options)

        pubmed_id = options['pubmed-id']
        lookup_publication_by_pubmed_id(pubmed_id)

        logger.info("Program finished successfully.")
