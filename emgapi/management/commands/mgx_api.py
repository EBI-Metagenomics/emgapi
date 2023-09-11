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
    'dev': 'http://wp-np2-5c:8080/ena/registry/metagenome/api/'
}
TOKEN = 'mgx 3D70473ED7C443CA9E97749F62FFCC5D'

RETRY_COUNT = 5

class Command(BaseCommand):
    help = "Check and populate metagenomics exchange."
    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "-s",
            "--study",
            action="store",
            required=False,
            type=str,
            help="Study accession (rather than all)",
        )
        parser.add_argument(
            "-p",
            "--pipeline",
            help="Pipeline version (rather than all). Not applicable to Genomes.",
            action="store",
            dest="pipeline",
            choices=[1.0, 2.0, 3.0, 4.0, 4.1, 5.0],
            required=False,
            type=float,
        )
        parser.add_argument(
            "-z",
            "--assembly",
            action="store",
            required=False,
            type=str,
            help="Assembly accession (rather than all)",
            nargs="+"
        )
        parser.add_argument(
            "-r",
            "--run",
            action="store",
            required=False,
            type=str,
            help="Run accession (rather than all)",
            nargs="+"
        )
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

    def _check_analysis(self, sourceID, public):
        params = {
            'status': 'public' if public else 'private',
        }
        response = self.get_request(url=self.check_url, params=params)
        exists = False
        if not response.ok:
            logging.error(
                "Error retrieving dataset {}, response code: {}".format(
                    self.check_url, response.status_code
                )
            )
        else:
            data = response.json()['datasets']
            for item in data:
                if item['sourceID'] == sourceID:
                    exists = True
        return exists

    def _post_request(self, url, data):
        default = {
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        }
        if self.auth:
            default["headers"].update(self.auth)
            response = requests.post(
                url, json=data, **default
            )
        else:
            logging.warning(
                "Not authenticated to POST private data."
                # noqa: E501
            )
            response = requests.post(
                url, json=data, **default
            )
        return response

    def _filtering_analyses(self):
        analyses = AnalysisJob.objects.all()
        if self.study_accession:
            analyses = analyses.filter(study__secondary_accession=self.study_accession)
        if self.run_accession:
            analyses = analyses.filter(run__accession=self.run_accession)
        if self.assembly_accession:
            analyses = analyses.filter(assembly__accession=self.assembly_accession)
        if self.pipeline_version:
            analyses = analyses.filter(pipeline__pipeline_id=self.pipeline_version)
        return analyses
    def handle(self, *args, **options):
        self.auth = None
        self.url = API['dev']
        self.broker = options.get("broker")
        self.check_url = self.url + f'brokers/{self.broker}/datasets'

        self.study_accession = options.get("study")
        self.pipeline_version = options.get("pipeline")
        self.assembly_accession = options.get("assembly")
        self.run_accession = options.get("run")

        analyses = self._filtering_analyses()
        for analysis in analyses:
            MGYA = analysis.accession
            public = not analysis.is_private
            if not public:
                self.auth = {"Authorization": TOKEN}
            # check is MGYA in ME
            if (self._check_analysis(sourceID=MGYA, public=public)):
                logging.info(f"{MGYA} exists in ME")
            else:
                logging.info(f"{MGYA} does not exist in ME")
                data = {
                    'confidence': 'full',
                    'endPoint': f'https://www.ebi.ac.uk/metagenomics/analyses/{MGYA}',
                    'method': ['other_metadata'],
                    'sourceID': MGYA,
                    'sequenceID': analysis.run.accesison,
                    'status': 'public' if public else 'private'
                }
                #self._post_request(url=self.url+'datasets', data=data)



