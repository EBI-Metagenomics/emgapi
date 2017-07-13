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


class TestPermissionsAPI(APITestCase):

    def setUp(self):
        _biome = mommy.make('emg_api.Biome', biome_name="foo",
                            lineage="root:foo", pk=123)

        # Webin-000 public
        mommy.make("emg_api.Study", pk=111, accession="SRP0111", is_public=1,
                   submission_account_id='Webin-000', biome=_biome)
        mommy.make("emg_api.Study", pk=112, accession="SRP0112", is_public=1,
                   submission_account_id='Webin-000', biome=_biome)
        # Webin-000 private
        mommy.make("emg_api.Study", pk=113, accession="SRP0113", is_public=0,
                   submission_account_id='Webin-000', biome=_biome)

        # Webin-111 public
        mommy.make("emg_api.Study", pk=114, accession="SRP0114", is_public=1,
                   submission_account_id='Webin-111', biome=_biome)
        # Webin-111 private
        mommy.make("emg_api.Study", pk=115, accession="SRP0115", is_public=0,
                   submission_account_id='Webin-111', biome=_biome)

        # unknown public
        mommy.make("emg_api.Study", pk=120, accession="SRP0120", is_public=1,
                   submission_account_id=None, biome=_biome)
        # unknown private
        mommy.make("emg_api.Study", pk=121, accession="SRP0121", is_public=0,
                   submission_account_id=None, biome=_biome)

    def test_public(self):
        url = reverse("emg_api:studies-list")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        # Meta
        assert rsp['meta']['pagination']['page'] == 1
        assert rsp['meta']['pagination']['pages'] == 1
        assert rsp['meta']['pagination']['count'] == 4

        # Data
        assert len(rsp['data']) == 4
        ids = set(['111', '112', '114', '120'])
        assert ids - set([d['id'] for d in rsp['data']]) == set()

        bad_ids = ['113', '115', '121']
        ids.update(bad_ids)
        assert ids - set([d['id'] for d in rsp['data']]) == set(bad_ids)

    def test_private(self):
        self.client.login(username='Webin-000', password='secret')

        url = reverse("emg_api:studies-list")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        # Meta
        assert rsp['meta']['pagination']['page'] == 1
        assert rsp['meta']['pagination']['pages'] == 1
        assert rsp['meta']['pagination']['count'] == 5

        # Data
        assert len(rsp['data']) == 5
        ids = set(['111', '112', '113', '114', '120'])
        assert ids - set([d['id'] for d in rsp['data']]) == set()

        bad_ids = ['115', '121']
        ids.update(bad_ids)
        assert ids - set([d['id'] for d in rsp['data']]) == set(bad_ids)
