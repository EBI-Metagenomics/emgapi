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
class TestTaxonomy(object):

    def test_organism_list(self, client, run):
        assert run.accession == 'ABC01234'
        call_command('import_taxonomy', run.accession,
                     os.path.dirname(os.path.abspath(__file__)))

        url = reverse("emgapi_v1:organisms-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp['data']) == 8

        expected = [
            'Bacteria', 'OPB56', 'Proteobacteria', 'Alphaproteobacteria',
            'RhodobacteralesRhodobacteraceae', 'Sphingomonadales',
            'XanthomonadalesXanthomonadaceae', 'Unusigned'
        ]
        ids = [a['attributes']['name'] for a in rsp['data']]
        assert ids == expected

    def test_organisms_tree(self, client, run):
        assert run.accession == 'ABC01234'
        call_command('import_taxonomy', run.accession,
                     os.path.dirname(os.path.abspath(__file__)))

        url = reverse("emgapi_v1:organisms-children-list",
                      args=['Bacteria:Proteobacteria:Alphaproteobacteria'])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp['data']) == 3

        expected = [
            'Bacteria:Proteobacteria:Alphaproteobacteria',
            ('Bacteria:Proteobacteria:Alphaproteobacteria'
             ':RhodobacteralesRhodobacteraceae'),
            ('Bacteria:Proteobacteria:Alphaproteobacteria'
             ':Sphingomonadales')
        ]
        ids = [a['id'] for a in rsp['data']]
        assert ids == expected

    def test_object_does_not_exist(self, client):
        url = reverse("emgapi_v1:organisms-children-list", args=['abc'])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_empty(self, client, run_emptyresults):
        job = run_emptyresults.accession
        version = run_emptyresults.pipeline.release_version
        assert job == 'EMPTY_ABC01234'

        call_command('import_taxonomy', job,
                     os.path.dirname(os.path.abspath(__file__)))

        url = reverse("emgapi_v1:runs-pipelines-taxonomy-list",
                      args=[job, version])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        assert len(rsp['data']) == 0

    def test_relations(self, client, run):
        call_command('import_taxonomy', run.accession,
                     os.path.dirname(os.path.abspath(__file__)))

        url = reverse("emgapi_v1:runs-pipelines-taxonomy-list",
                      args=[run.accession, run.pipeline.release_version])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        assert len(rsp['data']) == 8

        expected = {
            'Bacteria': 20, 'OPB56': 1, 'Proteobacteria': 15,
            'Alphaproteobacteria': 50, 'RhodobacteralesRhodobacteraceae': 42,
            'Sphingomonadales': 1, 'XanthomonadalesXanthomonadaceae': 2,
            'Unusigned': 319}

        ids = {
            a['attributes']['name']: a['attributes']['count']
            for a in rsp['data']
        }
        assert ids == expected
