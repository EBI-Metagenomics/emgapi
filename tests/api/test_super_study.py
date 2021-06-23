#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2020 EMBL - European Bioinformatics Institute
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

from test_utils.emg_fixtures import *  # noqa


@pytest.mark.django_db
class TestSuperStudyAPI:

    def test_details_by_id(self, client, super_study):
        url = reverse('emgapi_v1:super-studies-detail', args=['1'])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        # Data
        assert len(rsp) == 1
        assert rsp['data']['type'] == 'super-studies'
        assert rsp['data']['id'] == '1'
        _attr = rsp['data']['attributes']
        assert len(_attr) == 6
        assert _attr['super-study-id'] == 1
        assert _attr['title'] == 'Human Microbiome'
        assert _attr['description'] == 'Just a test description'
        assert _attr['biomes-count'] == 1
        assert _attr['url-slug'] == 'human-micro'

    def test_details_by_slug(self, client, super_study):
        url = reverse('emgapi_v1:super-studies-detail', args=['human-micro'])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        # Data
        assert len(rsp) == 1
        assert rsp['data']['type'] == 'super-studies'
        assert rsp['data']['id'] == '1'
        _attr = rsp['data']['attributes']
        assert len(_attr) == 6
        assert _attr['super-study-id'] == 1
        assert _attr['title'] == 'Human Microbiome'
        assert _attr['description'] == 'Just a test description'
        assert _attr['biomes-count'] == 1
        assert _attr['url-slug'] == 'human-micro'

    def test_public(self, client, super_study):
        url = reverse('emgapi_v1:super-studies-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        # Meta
        assert rsp['meta']['pagination']['page'] == 1
        assert rsp['meta']['pagination']['pages'] == 1
        assert rsp['meta']['pagination']['count'] == 1

        # Data
        assert len(rsp['data']) == 1

        d = rsp['data'][0]
        assert d['type'] == 'super-studies'
        assert d['id'] == '1'
        _attr = d['attributes']
        assert len(_attr) == 6
        assert _attr['super-study-id'] == 1
        assert _attr['title'] == 'Human Microbiome'
        assert _attr['description'] == 'Just a test description'
        assert _attr['biomes-count'] == 1
        assert _attr['url-slug'] == 'human-micro'
