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

from django.core.urlresolvers import reverse

from rest_framework import status

from test_utils.emg_fixtures import *  # noqa


@pytest.mark.django_db
class TestSampleAPI(object):

    def test_details(self, client, sample):
        url = reverse("emgapi:samples-detail", args=["ERS01234"])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        # Data
        assert len(rsp) == 1
        assert rsp['data']['type'] == "samples"
        assert rsp['data']['id'] == "ERS01234"
        _attr = rsp['data']['attributes']
        assert(len(_attr) == 18)
        assert _attr['accession'] == "ERS01234"
        assert _attr['biosample'] == "SAMS01234"
        assert _attr['sample-desc'] == "abcdefghijklmnoprstuvwyz"
        assert _attr['analysis-completed'] == "1970-01-01"
        assert _attr['collection-date'] == "1970-01-01"
        assert _attr['geo-loc-name'] == "Geo Location"
        assert not _attr['environment-biome']
        assert _attr['environment-feature'] == "abcdef"
        assert _attr['environment-material'] == "abcdef"
        assert _attr['sample-name'] == "Example sample name ERS01234"
        assert _attr['sample-alias'] == "ERS01234"
        assert not _attr['host-tax-id']
        assert _attr['species'] == "homo sapiense"
        assert _attr['latitude'] == 12.3456
        assert _attr['longitude'] == 456.456

    def test_public(self, client, sample, sample_private):
        url = reverse("emgapi:samples-list")
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
        assert d['type'] == "samples"
        assert d['id'] == "ERS01234"
        assert d['attributes']['accession'] == "ERS01234"
