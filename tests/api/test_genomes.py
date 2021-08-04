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
    def test_catalogue_creation(self, apiclient, biome_human, genome_catalogue_series, staff_user, public_user):
        # Fails if unauthenticated
        url = reverse('emgapi_v1:genome-catalogues-list')
        response = apiclient.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Fails for non-staff user
        apiclient.force_authenticate(public_user)
        response = apiclient.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Doesn't fail for auth reasons for staff user
        apiclient.force_authenticate(staff_user)
        response = apiclient.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Can create new catalogue
        response = apiclient.post(url, data={
            'biome': {'id': biome_human.biome_id, 'type': 'biomes'},
            'catalogue_id': 'new-cat-1-1',
            'catalogue_series': {'id': genome_catalogue_series.catalogue_series_id, 'type': 'genome-catalogue-series'},
            'name': 'New Cat v1.1',
            'version': '1.1',
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert emg_models.GenomeCatalogue.objects.filter(catalogue_id='new-cat-1-1').exists()

    def test_catalogue_creation_accession_numbers(self, apiclient, biome_human, genome_catalogue_series, staff_user):
        url = reverse('emgapi_v1:genome-catalogues-list')
        apiclient.force_authenticate(staff_user)

        # Can create new catalogue and get suggested accession numbers
        response = apiclient.post(url, data={
            'biome': {'id': biome_human.biome_id, 'type': 'biomes'},
            'catalogue_id': 'new-cat-1-2',
            'catalogue_series': {'id': genome_catalogue_series.catalogue_series_id, 'type': 'genome-catalogue-series'},
            'name': 'New Cat v1.2',
            'version': '1.2',
            'intended_genome_count': 1000
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert emg_models.GenomeCatalogue.objects.filter(catalogue_id='new-cat-1-2').exists()
        rsp = response.json()
        assert rsp['data']['attributes']['suggested-min-accession-number'] == 1
        assert rsp['data']['attributes']['suggested-max-accession-number'] == 1001

        # Next catalogue gets non-overlapping accessions even though no genomes present yet
        response = apiclient.post(url, data={
            'biome': {'id': biome_human.biome_id, 'type': 'biomes'},
            'catalogue_id': 'new-cat-1-3',
            'catalogue_series': {'id': genome_catalogue_series.catalogue_series_id, 'type': 'genome-catalogue-series'},
            'name': 'New Cat v1.3',
            'version': '1.3',
            'intended_genome_count': 500
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert emg_models.GenomeCatalogue.objects.filter(catalogue_id='new-cat-1-3').exists()
        rsp = response.json()
        assert rsp['data']['attributes']['suggested-min-accession-number'] == 1002
        assert rsp['data']['attributes']['suggested-max-accession-number'] == 1502

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
        assert rsp['data']['relationships']['biome']['data']['id'] == 'root:Host-associated:Human'

    def test_catalogue_genomes(self, client, genome_catalogue, genome):
        genome.catalogues.add(genome_catalogue)
        url = reverse('emgapi_v1:genome-catalogue-genomes-list', args=('mandalor-1-0',))
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp['data']) == 1
        assert rsp['meta']['pagination']['page'] == 1
        assert rsp['meta']['pagination']['pages'] == 1
        assert rsp['meta']['pagination']['count'] == 1
        assert rsp['data'][0]['type'] == 'genomes'
        assert rsp['data'][0]['id'] == 'MGYG00000001'
        assert rsp['data'][0]['attributes']['genome-id'] == 1
        assert rsp['data'][0]['attributes']['accession'] == 'MGYG00000001'
        assert rsp['data'][0]['attributes']['taxon-lineage'] == 'd__Test;'
