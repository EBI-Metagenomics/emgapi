#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2017-2022 EMBL - European Bioinformatics Institute
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
import requests

from django.db.models import Count
from django.core.management import BaseCommand
from django.conf import settings

from emgapi.models import Assembly, AnalysisJob

logger = logging.getLogger(__name__)
API = {
    'real': 'https://www.ebi.ac.uk/ena/registry/metagenome/api/',
    'dev': 'http://wp-np2-5c.ebi.ac.uk:8080/ena/registry/metagenome/api/'
}
TOKEN = 'mgx 3D70473ED7C443CA9E97749F62FFCC5D'

RETRY_COUNT = 5

class Command(BaseCommand):
    help = "Populate DB with existing metagenomics exchange"
    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)

        parser.add_argument(
            "--dev",
            action="store_true",
            required=False,
            help="Populate dev API",
        )
        parser.add_argument(
            "-b",
            "--broker",
            action="store",
            required=False,
            type=str,
            default='EMG',
            help="Broker name",
            choices=["EMG", "MAR"],
        )
    def get_request(self, url, params):
        if self.auth:
            response = requests.get(url, params=params, headers=self.auth)
        else:
            logging.warning(
                "Not authenticated to get private data."
                # noqa: E501
            )
            response = requests.get(url, params=params)
        return response

    def handle(self, *args, **options):
        self.auth = None
        self.url = API['dev']
        self.broker = options.get("broker")
        self.check_url = self.url + f'brokers/{self.broker}/datasets'


