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

from model_mommy import mommy

from test_utils.emg_fixtures import * # noqa


@pytest.mark.django_db
class TestPermissionsAPI(object):

    @pytest.fixture(autouse=True)
    def setup_method(self, db):
        _biome = mommy.make('emgapi.Biome', biome_name="foo",
                            lineage="root:foo", pk=123)

        # Webin-000 public
        mommy.make("emgapi.Study", pk=111, accession="SRP0111", is_public=1,
                   submission_account_id='Webin-000', biome=_biome)
        mommy.make("emgapi.Study", pk=112, accession="SRP0112", is_public=1,
                   submission_account_id='Webin-000', biome=_biome)
        # Webin-000 private
        mommy.make("emgapi.Study", pk=113, accession="SRP0113", is_public=0,
                   submission_account_id='Webin-000', biome=_biome)

        # Webin-111 public
        mommy.make("emgapi.Study", pk=114, accession="SRP0114", is_public=1,
                   submission_account_id='Webin-111', biome=_biome)
        # Webin-111 private
        mommy.make("emgapi.Study", pk=115, accession="SRP0115", is_public=0,
                   submission_account_id='Webin-111', biome=_biome)

        # unknown public
        mommy.make("emgapi.Study", pk=120, accession="SRP0120", is_public=1,
                   submission_account_id=None, biome=_biome)
        # unknown private
        mommy.make("emgapi.Study", pk=121, accession="SRP0121", is_public=0,
                   submission_account_id=None, biome=_biome)

    @pytest.mark.parametrize(
        'view, username, count, ids, bad_ids',
        [
            # private
            ('emgapi_v1:studies-list', 'Webin-111', 5,
             ['SRP0111', 'SRP0112', 'SRP0114', 'SRP0115', 'SRP0120'],
             ['SRP0113', 'SRP0121']),
            # mydata
            ('emgapi_v1:mydata-list', 'Webin-111', 2,
             ['SRP0114', 'SRP0115'],
             []),
            # public
            ('emgapi_v1:studies-list', None, 4,
             ['SRP0111', 'SRP0112', 'SRP0114', 'SRP0120'],
             ['SRP0113', 'SRP0115', 'SRP0121']),
        ]
    )
    def test_list(self, apiclient, view, username, count, ids, bad_ids):
        auth = None
        if username is not None:
            data = {
                "username": username,
                "password": "secret",
            }
            rsp = apiclient.post(
                reverse('obtain_jwt_token_v1'), data=data, format='json')
            token = rsp.json()['data']['token']
            auth = 'Bearer {}'.format(token)

        url = reverse(view)
        if auth is not None:
            response = apiclient.get(url, HTTP_AUTHORIZATION=auth)
        else:
            response = apiclient.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        # Meta
        assert rsp['meta']['pagination']['page'] == 1
        assert rsp['meta']['pagination']['pages'] == 1
        assert rsp['meta']['pagination']['count'] == count

        # Data
        assert len(rsp['data']) == count
        assert set(ids) - set([d['id'] for d in rsp['data']]) == set()

        ids.extend(bad_ids)
        assert set(ids) - set([d['id'] for d in rsp['data']]) == set(bad_ids)

    def test_detail(self, apiclient):
        data = {
            "username": "Webin-000",
            "password": "secret",
        }
        rsp = apiclient.post(
            reverse('obtain_jwt_token_v1'), data=data, format='json')
        token = rsp.json()['data']['token']

        url = reverse("emgapi_v1:studies-detail", args=['SRP0113'])
        response = apiclient.get(
            url, HTTP_AUTHORIZATION='Bearer {}'.format(token))
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        assert rsp['data']['id'] == 'SRP0113'

        url = reverse("emgapi_v1:studies-detail", args=['SRP0115'])
        response = apiclient.get(
            url, HTTP_AUTHORIZATION='Bearer {}'.format(token))
        assert response.status_code == status.HTTP_404_NOT_FOUND

        url = reverse("emgapi_v1:studies-detail", args=['SRP0121'])
        response = apiclient.get(
            url, HTTP_AUTHORIZATION='Bearer {}'.format(token))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize('accession', ['SRP0113', 'SRP0115', 'SRP0121'])
    def test_not_found(self, apiclient, accession):
        url = reverse("emgapi_v1:studies-detail", args=[accession])
        response = apiclient.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
