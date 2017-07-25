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


# import pytest
from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from model_mommy import mommy

from emgapi import models as emg_models


class TestBiomeAPI(APITestCase):

    def setUp(self):
        self.data = {}
        self.data['biomes'] = []
        _biome = [
            {'lineage': 'root', 'depth': 1, 'lft': 1, 'rgt': 984},
            {'lineage': 'root:foo', 'depth': 2, 'lft': 2, 'rgt': 161},
            {'lineage': 'root:foo2', 'depth': 2, 'lft': 162, 'rgt': 513},
            {'lineage': 'root:foo:bar', 'depth': 3, 'lft': 3, 'rgt': 160},
            {'lineage': 'root:foo2:bar', 'depth': 3, 'lft': 163, 'rgt': 513},
        ]
        for b in _biome:
            self.data['biomes'].append(
                mommy.make(
                    'emgapi.Biome',
                    depth=b['depth'],
                    biome_name=b['lineage'].split(':')[-1],
                    lineage=b['lineage'],
                    lft=b['lft'],
                    rgt=b['rgt'],
                    pk=(_biome.index(b)+1))
            )
        self.data['studies'] = []
        for pk in range(1, len(_biome)+1):
            self.data['studies'].append(
                mommy.make(
                    'emgapi.Study',
                    biome=emg_models.Biome.objects.get(pk=pk),
                    pk=pk,
                    accession="SRP{:0>3}".format(pk),
                    is_public=1
                )
            )

    def test_default(self):
        url = reverse('emgapi:biomes-list', args=['root'])
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        # Data
        assert len(rsp['data']) == 2

        biomes = rsp['data']
        for b in biomes:
            assert b['type'] == 'Biome'
            assert b['id'] in ('root:foo', 'root:foo2')

        response = self.client.get(
            biomes[0]['relationships']['studies']['links']['related'])
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp['data']) == 2
        for s in rsp['data']:
            assert s['type'] == 'Study'
            assert s['id'] in ('SRP002', 'SRP004')
