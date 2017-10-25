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

from rest_framework import status
from rest_framework.test import APITestCase

from model_mommy import mommy


class TestStudyAPI(APITestCase):

    def setUp(self):
        self.data = {}
        self.data['date'] = datetime.now()
        _biome = mommy.make(
            'emgapi.Biome',
            biome_name="foo",
            lineage="root:foo",
            pk=123)
        self.data['studies'] = []
        self.data['studies'].append(
            mommy.make(
                'emgapi.Study',
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
                last_update=self.data['date'],
                submission_account_id="Webin-842",
                result_directory="2017/05/SRP01234",
                first_created=self.data['date'],
                project_id="PRJDB1234"
            )
        )
        # private
        mommy.make("emgapi.Study", pk=456, biome=_biome, is_public=0)

    def test_details(self):
        url = reverse("emgapi:studies-detail", args=["SRP01234"])
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        # Data
        assert len(rsp) == 1
        assert rsp['data']['type'] == "studies"
        assert rsp['data']['id'] == "SRP01234"
        _attr = rsp['data']['attributes']
        assert(len(_attr) == 9)
        assert _attr['accession'] == "SRP01234"
        assert _attr['centre-name'] == "Centre Name"
        assert not _attr['public-release-date']
        assert _attr['study-abstract'] == "abcdefghijklmnoprstuvwyz"
        assert _attr['study-name'] == "Example study name"
        # assert _attr['study_status'] == "FINISHED"
        assert _attr['data-origination'] == "HARVESTED"
        # assert _attr['last_update'] == str(self.data['date'])
        # assert _attr['first_created'] == str(self.data['date'])
        assert _attr['project-id'] == "PRJDB1234"

    def test_public(self):
        url = reverse("emgapi:studies-list")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        # Meta
        assert rsp['meta']['pagination']['page'] == 1
        assert rsp['meta']['pagination']['pages'] == 1
        assert rsp['meta']['pagination']['count'] == 1

        # Data
        assert len(rsp['data']) == 1

        for d in rsp['data']:
            assert d['type'] == "studies"
            assert d['id'] == "SRP01234"
            assert d['attributes']['accession'] == "SRP01234"
