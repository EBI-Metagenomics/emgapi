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

        expected = ['GO:0055114', 'GO:0008152', 'GO:0006810']
        ids = [a['id'] for a in rsp['data']]
        assert ids == expected

        url = reverse("emgapi:goterms-detail", args=['GO:0055114'])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert rsp['data']['id'] == 'GO:0055114'

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

        expected = ['GO:0055114', 'GO:0008152', 'GO:0006810',
                    'GO:0006412', 'GO:0009058', 'GO:0005975']
        ids = [a['id'] for a in rsp['data']]
        print(ids)
        assert ids == expected

        url = reverse("emgapi:goterms-detail", args=['GO:0055114'])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert rsp['data']['id'] == 'GO:0055114'

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

        expected = ['IPR006882', 'IPR008659', 'IPR007875',
                    'IPR033393', 'IPR015072', 'IPR024581']
        ids = [a['id'] for a in rsp['data']]
        assert ids == expected

        url = reverse("emgapi:interproidentifier-detail", args=['IPR006882'])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert rsp['data']['id'] == 'IPR006882'

    def test_object_does_not_exist(self, client):
        url = reverse("emgapi:goterms-detail", args=['GO:9999'])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        url = reverse("emgapi:interproidentifier-detail", args=['IPR9999'])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_relations(self, client, run):
        assert run.accession == 'ABC01234'
        call_command('import_summary', run.accession,
                     os.path.dirname(os.path.abspath(__file__)),
                     suffix='.go_slim')
        call_command('import_summary', run.accession,
                     os.path.dirname(os.path.abspath(__file__)),
                     suffix='.go')
        call_command('import_summary', run.accession,
                     os.path.dirname(os.path.abspath(__file__)),
                     suffix='.ipr')

        url = reverse("emgapi:runs-pipelines-goslim-list",
                      args=[run.accession, '1.0'])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp['data']) == 3

        expected = ['GO:0006810', 'GO:0008152', 'GO:0055114']
        ids = [a['id'] for a in rsp['data']]
        assert ids == expected

        url = reverse("emgapi:runs-pipelines-goterms-list",
                      args=[run.accession, '1.0'])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp['data']) == 6

        expected = ['GO:0005975', 'GO:0006412', 'GO:0006810',
                    'GO:0008152', 'GO:0009058', 'GO:0055114']
        ids = [a['id'] for a in rsp['data']]
        assert ids == expected

        url = reverse("emgapi:runs-pipelines-interpro-list",
                      args=[run.accession, '1.0'])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp['data']) == 6

        expected = ['IPR006882', 'IPR007875', 'IPR008659',
                    'IPR015072', 'IPR024581', 'IPR033393']
        ids = [a['id'] for a in rsp['data']]
        assert ids == expected
