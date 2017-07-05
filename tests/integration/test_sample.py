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
from datetime import datetime

from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase

from model_mommy import mommy

from emg_api.models import Sample  # noqa


class TestSampleAPI(APITestCase):
    def setUp(self):
        self.data = {}
        self.data['date'] = datetime.now()
        _biome = mommy.make(
            'emg_api.Biome',
            biome_name="foo",
            lineage="root:foo",
            pk=123)
        self.data['studies'] = []
        self.data['studies'].append(
            mommy.make(
                'emg_api.Sample',
                biome=_biome,
                pk=123,
                sample_desc="abcdefghijklmnoprstuvwyz",
                accession="DRS012345",
                analysis_completed=self.data['date'].date(),
                collection_date=self.data['date'].date(),
                geo_loc_name="Geo Location",
                is_public=1,
                metadata_received=self.data['date'],
                sequencedata_archived=self.data['date'],
                sequencedata_received=self.data['date'],
                environment_biome=None,
                environment_feature="abcdef",
                environment_material="abcdef",
                sample_name="DRS012345",
                sample_alias="DRS012345",
                host_tax_id=None,
                species=None,
                latitude="12.3456",
                longitude="123.4567",
                last_update=self.data['date'],
                submission_account_id="Webin-842"
            )
        )
        # private
        mommy.make("emg_api.Sample", pk=456, biome=_biome, is_public=0)

    def test_details(self):
        url = reverse("samples-detail", args=["DRS012345"])
        response = self.client.get(url)
        assert response.status_code == 200
        rsp = response.json()

        # Data
        assert len(rsp) == 1
        assert rsp['data']['type'] == "Sample"
        assert rsp['data']['id'] == "123"
        _attr = rsp['data']['attributes']
        assert(len(_attr) == 22)
        assert _attr['accession'] == "DRS012345"
        assert _attr['sample_desc'] == "abcdefghijklmnoprstuvwyz"
        assert _attr['biome_name'] == "foo"
        assert _attr['biome'] == "root:foo"
        assert _attr['analysis_completed'] == str(self.data['date'].date())
        assert _attr['collection_date'] == str(self.data['date'].date())
        assert _attr['geo_loc_name'] == "Geo Location"
        assert _attr['is_public'] == 1
        # assert _attr['metadata_received'] == str(self.data['date'])
        # assert _attr['sequencedata_archived'] == str(self.data['date'])
        # assert _attr['sequencedata_received'] == str(self.data['date'])
        assert not _attr['environment_biome']
        assert _attr['environment_feature'] == "abcdef"
        assert _attr['environment_material'] == "abcdef"
        assert _attr['sample_name'] == "DRS012345"
        assert _attr['sample_alias'] == "DRS012345"
        assert not _attr['host_tax_id']
        assert not _attr['species']
        assert _attr['latitude'] == "12.3456"
        assert _attr['longitude'] == "123.4567"
        # assert _attr['last_update'] == str(self.data['date'])
        assert _attr['submission_account_id'] == "Webin-842"

    def test_public(self):
        url = reverse("samples-list")
        response = self.client.get(url)
        assert response.status_code == 200
        rsp = response.json()

        # Meta
        assert rsp['meta']['pagination']['page'] == 1
        assert rsp['meta']['pagination']['pages'] == 1
        assert rsp['meta']['pagination']['count'] == 1

        # Data
        assert len(rsp['data']) == 1

        for d in rsp['data']:
            assert d['type'] == "Sample"
            assert d['id'] == "123"
            assert d['attributes']['accession'] == "DRS012345"
            assert d['attributes']['is_public'] == 1
