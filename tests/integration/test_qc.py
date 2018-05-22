#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2017 EMBL - European Bioinformatics Institute
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

import pytest
import os

from django.core.urlresolvers import reverse
from django.core.management import call_command

from rest_framework import status

# import fixtures
from test_utils.emg_fixtures import *  # noqa


@pytest.mark.usefixtures('mongodb')
@pytest.mark.django_db
class TestCLI(object):

    def test_qc(self, client, run):
        call_command('import_qc', 'ABC01234',
                     os.path.dirname(os.path.abspath(__file__)))

        url = reverse("emgapi_v1:analysis-detail",
                      args=["MGYA00001234"])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp['data']['attributes']['analysis-summary']) == 5

        expected = [
            {
                'key': 'Submitted nucleotide sequences',
                'value': '12345'
            },
            {
                'key': 'Nucleotide sequences after format-specific filtering',
                'value': '12345'
            },
            {
                'key': 'Predicted CDS',
                'value': '12345'
            },
            {
                'key': 'Predicted CDS with InterProScan match',
                'value': '12345'
            },
            {
                'key': 'Total InterProScan matches',
                'value': '12345678'
            }
        ]
        assert rsp['data']['attributes']['analysis-summary'] == expected

    @pytest.mark.parametrize(
        'results',
        ({
            'pipeline': '1.0',
            'accession': 'MGYA00001234',
            'expected': [
                {
                    'key': 'Submitted nucleotide sequences',
                    'value': '12345'
                },
                {
                    'key': ('Nucleotide sequences after format-specific '
                            'filtering'),
                    'value': '12345'
                },
                {
                    'key': 'Predicted CDS',
                    'value': '12345'
                },
                {
                    'key': 'Predicted CDS with InterProScan match',
                    'value': '12345'
                },
                {
                    'key': 'Total InterProScan matches',
                    'value': '12345678'
                }
            ]
        }, {
            'pipeline': '4.0',
            'accession': 'MGYA00005678',
            'expected': [
                {
                    'key': 'Submitted nucleotide sequences',
                    'value': '54321'
                },
                {
                    'key': ('Nucleotide sequences after format-specific '
                            'filtering'),
                    'value': '54321'
                },
                {
                    'key': 'Predicted CDS',
                    'value': '54321'
                },
                {
                    'key': 'Predicted CDS with InterProScan match',
                    'value': '54321'
                },
                {
                    'key': 'Total InterProScan matches',
                    'value': '87654321'
                }
            ]
        })
    )
    def test_qc_multiple_pipelines(self, client, run_multiple_analysis,
                                   results):
        call_command('import_qc', 'ABC01234',
                     os.path.dirname(os.path.abspath(__file__)),
                     pipeline='1.0')
        call_command('import_qc', 'ABC01234',
                     os.path.dirname(os.path.abspath(__file__)),
                     pipeline='4.0')

        url = reverse("emgapi_v1:analysis-detail",
                      args=[results['accession']])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp['data']['attributes']['analysis-summary']) == 5

        expected = results['expected']
        assert rsp['data']['attributes']['analysis-summary'] == expected

    def test_empty_qc(self, client, run_emptyresults):
        run = run_emptyresults.run.accession
        job = run_emptyresults.accession
        version = run_emptyresults.pipeline.release_version
        assert run == 'ABC01234'
        call_command('import_qc', job,
                     os.path.dirname(os.path.abspath(__file__)),
                     pipeline=version)

        url = reverse("emgapi_v1:analysis-detail",
                      args=[job])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp['data']['attributes']['analysis-summary']) == 0
