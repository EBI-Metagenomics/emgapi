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
class TestAnnotations(object):

    def test_goslim(self, client, run):
        assert run.accession == 'ABC01234'
        call_command('import_summary', run.accession,
                     os.path.dirname(os.path.abspath(__file__)),
                     suffix='.go_slim')

        url = reverse("emgapi:goterms-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp['data']) == 3

        expected = ['GO:0030246', 'GO:0046906', 'GO:0043167']
        ids = [a['id'] for a in rsp['data']]
        assert ids == expected

        url = reverse("emgapi:goterms-detail", args=['GO:0030246'])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert rsp['data']['id'] == 'GO:0030246'

    def test_go(self, client, run):
        assert run.accession == 'ABC01234'
        call_command('import_summary', run.accession,
                     os.path.dirname(os.path.abspath(__file__)),
                     suffix='.go')

        url = reverse("emgapi:goterms-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp['data']) == 6

        expected = ['GO:0030170', 'GO:0019842', 'GO:0030246',
                    'GO:0046906', 'GO:0043167', 'GO:0005515']
        ids = [a['id'] for a in rsp['data']]
        assert ids == expected

        url = reverse("emgapi:goterms-detail", args=['GO:0030170'])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert rsp['data']['id'] == 'GO:0030170'

    def test_ipr(self, client, run):
        assert run.accession == 'ABC01234'
        call_command('import_summary', run.accession,
                     os.path.dirname(os.path.abspath(__file__)),
                     suffix='.ipr')

        url = reverse("emgapi:interproidentifier-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp['data']) == 6

        expected = ['IPR009739', 'IPR021425', 'IPR021710',
                    'IPR033771', 'IPR024561', 'IPR013698']
        ids = [a['id'] for a in rsp['data']]
        assert ids == expected

        url = reverse("emgapi:interproidentifier-detail", args=['IPR009739'])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert rsp['data']['id'] == 'IPR009739'

    def test_object_does_not_exist(self, client):
        url = reverse("emgapi:goterms-detail", args=['GO:9999'])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        url = reverse("emgapi:interproidentifier-detail", args=['IPR9999'])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_empty(self, client, run_emptyresults):
        job = run_emptyresults.accession
        version = run_emptyresults.pipeline.release_version
        assert job == 'EMPTY_ABC01234'

        call_command('import_summary', job,
                     os.path.dirname(os.path.abspath(__file__)),
                     suffix='.go_slim')
        call_command('import_summary', job,
                     os.path.dirname(os.path.abspath(__file__)),
                     suffix='.go')
        call_command('import_summary', job,
                     os.path.dirname(os.path.abspath(__file__)),
                     suffix='.ipr')

        url = reverse("emgapi:runs-pipelines-goslim-list",
                      args=[job, version])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        assert len(rsp['data']) == 0

        url = reverse("emgapi:runs-pipelines-goterms-list",
                      args=[job, version])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        assert len(rsp['data']) == 0

        url = reverse("emgapi:runs-pipelines-interpro-list",
                      args=[job, version])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        assert len(rsp['data']) == 0

    @pytest.mark.parametrize(
        'pipeline_version', [
            {'version': '1.0', 'expected': {
                'go_slim': {
                    'GO:0030246': 23011, 'GO:0043167': 3222011,
                    'GO:0046906': 232611
                },
                'go_terms': {
                    'GO:0005515': 6016, 'GO:0019842': 1377,
                    'GO:0030170': 2885, 'GO:0030246': 230,
                    'GO:0043167': 32220, 'GO:0046906': 2326
                },
                'interpro': {
                    'IPR009739': 1, 'IPR013698': 6, 'IPR021425': 2,
                    'IPR021710': 3, 'IPR024561': 5, 'IPR033771': 4
                },
            }},
            {'version': '4.0', 'expected': {
                'go_slim': {
                    'GO:0005618': 1222, 'GO:0009276': 0,
                    'GO:0016020': 1414622
                },
                'go_terms': {
                    'GO:0005575': 67, 'GO:0005576': 37, 'GO:0005618': 12,
                    'GO:0009276': 0, 'GO:0016020': 14146, 'GO:0019867': 504
                },
                'interpro': {
                    'IPR006677': 3, 'IPR010326': 1, 'IPR011459': 6,
                    'IPR023385': 5, 'IPR024548': 2, 'IPR031692': 4
                },
            }}
        ]
    )
    def test_relations(self, client, analysis_results, pipeline_version):
        version = pipeline_version['version']
        job = analysis_results[version].accession
        call_command('import_summary', job,
                     os.path.dirname(os.path.abspath(__file__)),
                     suffix='.go_slim')
        call_command('import_summary', job,
                     os.path.dirname(os.path.abspath(__file__)),
                     suffix='.go')
        call_command('import_summary', job,
                     os.path.dirname(os.path.abspath(__file__)),
                     suffix='.ipr')

        url = reverse("emgapi:runs-pipelines-goslim-list",
                      args=[job, version])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        assert len(rsp['data']) == 3

        expected = pipeline_version['expected']['go_slim']
        ids = {
            a['attributes']['accession']: a['attributes']['count']
            for a in rsp['data']
        }
        assert ids == expected

        url = reverse("emgapi:runs-pipelines-goterms-list",
                      args=[job, version])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        assert len(rsp['data']) == 6

        expected = pipeline_version['expected']['go_terms']
        ids = {
            a['attributes']['accession']: a['attributes']['count']
            for a in rsp['data']
        }
        assert ids == expected

        url = reverse("emgapi:runs-pipelines-interpro-list",
                      args=[job, version])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        assert len(rsp['data']) == 6

        expected = pipeline_version['expected']['interpro']
        ids = {
            a['attributes']['accession']: a['attributes']['count']
            for a in rsp['data']
        }
        assert ids == expected
