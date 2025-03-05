#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2021 EMBL - European Bioinformatics Institute
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest

from django.urls import reverse

from rest_framework import status

from emgapi import models as emg_models

from test_utils.emg_fixtures import *  # noqa


@pytest.mark.django_db
class TestGenomesAPI:
    def test_catalogue_list(self, client, genome_catalogue):
        url = reverse('emgapi_v1:genome-catalogues-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp['data']) == 1
        assert rsp['data'][0]['id'] == 'mandalor-1-0'
        assert rsp['data'][0]['attributes']['name'] == 'Mandalorian Genomes v1.0'
        assert rsp['meta']['pagination']['page'] == 1
        assert rsp['meta']['pagination']['pages'] == 1
        assert rsp['meta']['pagination']['count'] == 1

    def test_catalogue_detail(self, client, genome_catalogue):
        url = reverse('emgapi_v1:genome-catalogues-detail', args=('mandalor-1-0',))
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert rsp['data']['type'] == 'genome-catalogues'
        assert rsp['data']['id'] == 'mandalor-1-0'
        _attr = rsp['data']['attributes']
        assert _attr['name'] == 'Mandalorian Genomes v1.0'
        assert _attr['version'] == '1.0'
        assert _attr['catalogue-type'] == 'eukaryotes'
        assert _attr['catalogue-biome-label'] == 'Mandalor'
        assert rsp['data']['relationships']['biome']['data']['id'] == 'root:Host-associated:Human'

    def test_catalogue_genomes(self, client, genome_catalogue, genome):
        url = reverse('emgapi_v1:genome-catalogue-genomes-list', args=('mandalor-1-0',))
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp['data']) == 1
        assert rsp['meta']['pagination']['page'] == 1
        assert rsp['meta']['pagination']['pages'] == 1
        assert rsp['meta']['pagination']['count'] == 1
        assert rsp['data'][0]['type'] == 'genomes'
        assert rsp['data'][0]['id'] == 'MGYG000000001'
        assert rsp['data'][0]['attributes']['genome-id'] == 1
        assert rsp['data'][0]['attributes']['accession'] == 'MGYG000000001'
        assert rsp['data'][0]['attributes']['taxon-lineage'] == 'd__Test;'
