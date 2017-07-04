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

import importlib
import pytest

from model_mommy import mommy

from django.core.urlresolvers import reverse


class TestDefaultAPI(object):

    @pytest.mark.parametrize(
        '_view',
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
    def test_empty_list(self, client, _view):
        view_name = "%s-list" % _view
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
        '_model, _view',
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
    def test_list(self, client, _model, _view):
        klass = getattr(importlib.import_module("emg_api.models"), _model)

        model_name = "emg_api.%s" % _model
        view_name = "%s-list" % _view

        # start from 1
        # https://code.djangoproject.com/ticket/17653
        for pk in range(1, 101):
            if _model in ('Sample', 'Study'):
                _biome = mommy.make('emg_api.Biome', pk=pk)
                mommy.make(model_name, pk=pk, biome=_biome, is_public=1)
            elif _model in ('Run'):
                mommy.make(model_name, pk=pk, run_status_id=4)
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
        first_link = 'http://testserver/api/%s?page=1' % _view
        last_link = 'http://testserver/api/%s?page=5' % _view
        next_link = 'http://testserver/api/%s?page=2' % _view
        assert rsp['links']['first'] == first_link
        assert rsp['links']['last'] == last_link
        assert rsp['links']['next'] == next_link
        assert rsp['links']['prev'] is None

        # Data
        assert len(rsp['data']) == 20

        for d in rsp['data']:
            assert d['type'] == _model
            _attrs = [f.name for f in klass._meta.get_fields()]
            for a in d['attributes']:
                assert a in _attrs
