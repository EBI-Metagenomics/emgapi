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
import random

from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase

from model_mommy import mommy


class TestBiomeAPI(APITestCase):

    def setUp(self):
        self.data = {}
        self.data['biomes'] = []
        _biome = [
            'root',
            'root:foo', 'root:foo2', 'root:foo3', 'root:foo4', 'root:foo5',
            'root:foo:bar', 'root:foo:bar2', 'root:foo:bar3',
            'root:foo:bar4', 'root:foo:bar4'
        ]
        for b in _biome:
            self.data['biomes'].append(
                mommy.make(
                    'emg_api.Biome',
                    biome_name=b,
                    lineage=b,
                    pk=(_biome.index(b)+1))
            )
        self.data['studies'] = []
        for pk in range(1, 51):
            self.data['studies'].append(
                mommy.make(
                    'emg_api.Study',
                    biome=random.sample(self.data['biomes'], 1)[0],
                    pk=pk,
                    accession="SRP{:0>3}".format(pk),
                    is_public=1
                )
            )

    def test_default(self):
        url = reverse('biomes-top10')
        response = self.client.get(url)
        assert response.status_code == 200
        rsp = response.json()

        # Data
        assert len(rsp['data']) == 10
