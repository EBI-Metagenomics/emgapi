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
from django.urls.exceptions import NoReverseMatch

from rest_framework import status


class TestDefaultAPI(object):

    def test_default(self, client):
        url = reverse('emgapi:api-root')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        expected = {
            # TODO: create alias
            # "biomes": "http://testserver/api/biomes",
            "studies": "http://testserver/api/studies",
            "samples": "http://testserver/api/samples",
            "runs": "http://testserver/api/runs",
            "pipelines": "http://testserver/api/pipelines",
            "experiments": "http://testserver/api/experiments",
            "publications": "http://testserver/api/publications",
            'tools': 'http://testserver/api/tools',
            "mydata": "http://testserver/api/mydata",
        }
        assert rsp['data'] == expected

    @pytest.mark.parametrize(
        '_view',
        [
            # TODO: create alias
            # 'emgapi:biomes',
            'emgapi:experiments',
            'emgapi:pipelines',
            'emgapi:publications',
            'emgapi:samples',
            'emgapi:runs',
            'emgapi:studies',
            'emgapi:tools',
            pytest.mark.xfail('viewdoesnotexist', raises=NoReverseMatch),
        ]
    )
    @pytest.mark.django_db
    def test_empty_list(self, client, _view):
        view_name = "%s-list" % _view
        url = reverse(view_name)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert rsp['meta']['pagination']['page'] == 1
        assert rsp['meta']['pagination']['pages'] == 1
        assert rsp['meta']['pagination']['count'] == 0

    @pytest.mark.parametrize(
        '_model, _view, relations',
        [
            ('ExperimentType', 'emgapi:experiments', ['samples']),
            ('Pipeline', 'emgapi:pipelines', ['samples', 'tools']),
            ('Publication', 'emgapi:publications', ['studies']),
            ('Run', 'emgapi:runs', ['pipelines', 'experiment_type', 'sample']),
            ('Sample', 'emgapi:samples',
             ['biome', 'study', 'runs', 'metadata']),
            ('Study', 'emgapi:studies', ['biomes', 'publications', 'samples']),
            ('PipelineTool', 'emgapi:tools', ['pipelines']),
        ]
    )
    @pytest.mark.django_db
    def test_list(self, client, _model, _view, relations):
        model_name = "emgapi.%s" % _model
        view_name = "%s-list" % _view

        # start from 1
        # https://code.djangoproject.com/ticket/17653
        for pk in range(1, 101):
            if _model in ('Sample', 'Study'):
                _biome = mommy.make('emgapi.Biome', pk=pk)
                mommy.make(model_name, pk=pk, biome=_biome, is_public=1)
            elif _model in ('Run',):
                _as = mommy.make('emgapi.AnalysisStatus', pk=3)
                _p = mommy.make('emgapi.Pipeline', pk=1,
                                release_version="1.0")
                mommy.make('emgapi.AnalysisJob',
                           pk=pk, pipeline=_p, analysis_status=_as)
            elif _model in ('PipelineTool',):
                _p = mommy.make('emgapi.Pipeline', pk=pk,
                                release_version="1.0")
                _t = mommy.make('emgapi.PipelineTool', pk=pk,
                                tool_name='ToolName')
                mommy.make('emgapi.PipelineReleaseTool', pk=pk,
                           pipeline=_p, tool=_t)
            else:
                mommy.make(model_name, pk=pk)

        url = reverse(view_name)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        # Meta
        assert rsp['meta']['pagination']['page'] == 1
        assert rsp['meta']['pagination']['pages'] == 5
        assert rsp['meta']['pagination']['count'] == 100

        # Links
        _view_url = _view.split(":")[1]
        first_link = 'http://testserver/api/%s?page=1' % _view_url
        last_link = 'http://testserver/api/%s?page=5' % _view_url
        next_link = 'http://testserver/api/%s?page=2' % _view_url
        assert rsp['links']['first'] == first_link
        assert rsp['links']['last'] == last_link
        assert rsp['links']['next'] == next_link
        assert rsp['links']['prev'] is None

        # Data
        assert len(rsp['data']) == 20

        for d in rsp['data']:
            assert d['type'] == _model
            assert 'attributes' in d
            assert 'relationships' in d
            assert set(d['relationships']) - set(relations) == set()
