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

# import fixtures
from test_utils.emg_fixtures import *  # noqa


@pytest.mark.django_db
class TestStudyAPI(object):

    def test_details(self, client, study):
        url = reverse("emgapi_v1:studies-detail", args=["MGYS00001234"])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        # Data
        assert len(rsp) == 1
        assert rsp['data']['type'] == "studies"
        assert rsp['data']['id'] == "MGYS00001234"
        _attr = rsp['data']['attributes']
        assert(len(_attr) == 10)
        assert _attr['accession'] == "MGYS00001234"
        assert _attr['secondary-accession'] == "SRP01234"
        assert _attr['centre-name'] == "Centre Name"
        assert not _attr['public-release-date']
        assert _attr['study-abstract'] == "abcdefghijklmnoprstuvwyz"
        assert _attr['study-name'] == "Example study name SRP01234"
        assert _attr['data-origination'] == "HARVESTED"
        assert _attr['last-update'] == "1970-01-01T00:00:00"
        assert _attr['bioproject'] == "PRJDB1234"

    def test_public(self, client, study, study_private):
        url = reverse("emgapi_v1:studies-list")
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
        assert d['type'] == "studies"
        assert d['id'] == "MGYS00001234"
        assert d['attributes']['accession'] == "MGYS00001234"
