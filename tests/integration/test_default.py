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

from model_mommy import mommy

from django.core.urlresolvers import reverse

from emg_api.models import Biome  # noqa
from emg_api.models import ExperimentType  # noqa
from emg_api.models import Pipeline  # noqa
from emg_api.models import Publication  # noqa
from emg_api.models import Run  # noqa
from emg_api.models import Sample  # noqa
from emg_api.models import Study  # noqa


class TestDefaultAPI(object):

    @pytest.mark.parametrize(
        'emg_view',
        [
            'biomes',
            'experiments',
            'pipelines',
            'publications',
            'samples',
            'studies',
            pytest.mark.xfail('viewdoesnotexist'),
        ]
    )
    @pytest.mark.django_db
    def test_empty_list(self, client, emg_view):
        view_name = "%s-list" % emg_view
        url = reverse(view_name)
        response = client.get(url)
        assert response.status_code == 200
        # assert response.headers['Content-Type'] == \
        # 'application/vnd.api+json'
        rsp = response.json()
        assert rsp['meta']['pagination']['page'] == 1
        assert rsp['meta']['pagination']['pages'] == 1
        assert rsp['meta']['pagination']['count'] == 0

    @pytest.mark.parametrize(
        'emg_model, emg_view',
        [
            ('Biome', 'biomes'),
            ('ExperimentType', 'experiments'),
            ('Pipeline', 'pipelines'),
            ('Publication', 'publications'),
            ('Run', 'runs'),
            ('Sample', 'samples'),
            ('Study', 'studies'),
        ]
    )
    @pytest.mark.django_db
    def test_list(self, client, emg_model, emg_view):
        model_name = "emg_api.%s" % emg_model
        view_name = "%s-list" % emg_view

        for pk in range(0, 100):
            if emg_model in ('Sample', 'Study'):
                _biome = mommy.make('emg_api.Biome', pk=pk)
                mommy.make(model_name, pk=pk, biome=_biome)
            else:
                mommy.make(model_name, pk=pk)

        url = reverse(view_name)
        response = client.get(url)
        assert response.status_code == 200
        rsp = response.json()

        # Meta
        assert rsp['meta']['pagination']['page'] == 1
        assert rsp['meta']['pagination']['pages'] == 5
        assert rsp['meta']['pagination']['count'] == 100

        # Links
        first_link = 'http://testserver/api/%s?page=1' % emg_view
        last_link = 'http://testserver/api/%s?page=5' % emg_view
        next_link = 'http://testserver/api/%s?page=2' % emg_view
        assert rsp['links']['first'] == first_link
        assert rsp['links']['last'] == last_link
        assert rsp['links']['next'] == next_link
        assert rsp['links']['prev'] is None

        # Data
        assert len(rsp['data']) == 20
