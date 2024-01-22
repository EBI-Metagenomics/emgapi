#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime

# Copyright 2020 EMBL - European Bioinformatics Institute
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

from django.urls import reverse

from rest_framework import status

from test_utils.emg_fixtures import *  # noqa


@pytest.mark.django_db
class TestStudyAPI:

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
        assert(len(_attr) == 11)
        assert _attr['accession'] == "MGYS00001234"
        assert _attr['secondary-accession'] == "SRP01234"
        assert _attr['centre-name'] == "Centre Name"
        assert not _attr['public-release-date']
        assert _attr['study-abstract'] == "abcdefghijklmnoprstuvwyz"
        assert _attr['study-name'] == "Example study name SRP01234"
        assert _attr['data-origination'] == "HARVESTED"
        assert _attr['last-update'][:4] == datetime.datetime.now().isoformat()[:4]
        assert _attr['bioproject'] == "PRJDB1234"
        assert _attr['is-private'] == False

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

    def test_csv(self, client, studies):
        url = reverse("emgapi_v1:studies-list", kwargs={'format': 'csv'})
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.get('Content-Disposition') == 'attachment; filename="Study.csv"'
        content = b''.join(response.streaming_content).decode('utf-8')

        expected_header = [
            "\"accession\"",
            "\"analyses\"",
            "\"bioproject\"",
            "\"centre_name\"",
            "\"data_origination\"",
            "\"downloads\"",
            "\"is_private\"",
            "\"last_update\"",
            "\"public_release_date\"",
            "\"publications\"",
            "\"samples\"",
            "\"samples_count\"",
            "\"secondary_accession\"",
            "\"study_abstract\"",
            "\"study_name\"",
            "\"url\""
        ]
        first_row = [
            "MGYS00000001",
            "",
            "PRJDB0001",
            "Centre Name",
            "HARVESTED",
            "",
            "False",
            None,
            "",
            "",
            "",
            "",
            "SRP0001",
            "",
            "Example study name 1",
            "http://testserver/v1/studies/MGYS00000001.csv"
        ]

        rows = content.splitlines()

        assert len(rows) == 50

        assert expected_header == rows[0]
        first_row_response = rows[1].split(',')
        assert len(first_row_response) == len(first_row)
        for response_element, expected_element in zip(first_row_response, first_row):
            if expected_element is not None:
                assert response_element == expected_element

