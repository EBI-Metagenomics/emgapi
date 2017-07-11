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


class TestStudyAPI(APITestCase):

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
                'emg_api.Study',
                biome=_biome,
                pk=123,
                study_abstract="abcdefghijklmnoprstuvwyz",
                accession="SRP01234",
                centre_name="Centre Name",
                is_public=1,
                public_release_date=None,
                study_name="Example study name",
                study_status="FINISHED",
                data_origination="HARVESTED",
                author_email=None,
                author_name=None,
                last_update=self.data['date'],
                submission_account_id="Webin-842",
                result_directory="2017/05/SRP01234",
                first_created=self.data['date'],
                project_id="PRJDB1234"
            )
        )
        # private
        mommy.make("emg_api.Study", pk=456, biome=_biome, is_public=0)

    def test_details(self):
        url = reverse("emg_api:studies-detail", args=["SRP01234"])
        response = self.client.get(url)
        assert response.status_code == 200
        rsp = response.json()

        # Data
        assert len(rsp) == 1
        assert rsp['data']['type'] == "Study"
        assert rsp['data']['id'] == "123"
        _attr = rsp['data']['attributes']
        assert(len(_attr) == 14)
        assert _attr['accession'] == "SRP01234"
        assert _attr['biome_name'] == "foo"
        assert _attr['biome'] == "root:foo"
        assert _attr['centre_name'] == "Centre Name"
        assert not _attr['public_release_date']
        assert _attr['study_abstract'] == "abcdefghijklmnoprstuvwyz"
        assert _attr['study_name'] == "Example study name"
        assert _attr['study_status'] == "FINISHED"
        assert _attr['data_origination'] == "HARVESTED"
        assert not _attr['author_email']
        assert not _attr['author_name']
        # assert _attr['last_update'] == str(self.data['date'])
        # assert _attr['first_created'] == str(self.data['date'])
        assert _attr['project_id'] == "PRJDB1234"

    def test_public(self):
        url = reverse("emg_api:studies-list")
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
            assert d['type'] == "Study"
            assert d['id'] == "123"
            assert d['attributes']['accession'] == "SRP01234"
