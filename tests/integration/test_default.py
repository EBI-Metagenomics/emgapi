#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2017 EMBL - European Bioinformatics Institute
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

from model_mommy import mommy

from django.core.urlresolvers import reverse
from django.urls.exceptions import NoReverseMatch

from rest_framework import status

# import fixtures
from test_utils.emg_fixtures import *  # noqa


class TestDefaultAPI(object):

    def test_default(self, client, api_version):
        url = reverse('emgapi_v1:api-root')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        host = 'http://testserver/%s' % api_version
        expected = {
            'biomes': '%s/biomes' % host,
            'studies': '%s/studies' % host,
            'samples': '%s/samples' % host,
            'runs': '%s/runs' % host,
            'analyses': '%s/analyses' % host,
            'assemblies': '%s/assemblies' % host,
            'pipelines': '%s/pipelines' % host,
            'experiment-types': '%s/experiment-types' % host,
            'publications': '%s/publications' % host,
            'pipeline-tools': '%s/pipeline-tools' % host,
            'annotations/go-terms': '%s/annotations/go-terms' % host,
            'annotations/interpro-identifiers':
                '%s/annotations/interpro-identifiers' % host,
            'annotations/organisms': '%s/annotations/organisms' % host,
            'mydata': '%s/mydata' % host,
            'genomes': '%s/genomes' % host,
            'cogs': '%s/cogs' % host,
            'genomeset': '%s/genomeset' % host,
            'kegg-classes': '%s/kegg-classes' % host,
            'kegg-modules': '%s/kegg-modules' % host,
            'release': '%s/release' % host
        }
        assert rsp['data'] == expected

    @pytest.mark.parametrize(
        '_view',
        [
            'emgapi_v1:biomes',
            'emgapi_v1:experiment-types',
            'emgapi_v1:pipelines',
            'emgapi_v1:publications',
            'emgapi_v1:samples',
            'emgapi_v1:runs',
            'emgapi_v1:analyses',
            'emgapi_v1:studies',
            'emgapi_v1:pipeline-tools',
            'emgapi_v1:goterms',
            'emgapi_v1:interproidentifier',
            'emgapi_v1:organisms',
            'emgapi_v1:genomes'
        ]
    )
    @pytest.mark.django_db
    def test_empty_list(self, client, _view):
        view_name = '%s-list' % _view
        url = reverse(view_name)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert rsp['meta']['pagination']['page'] == 1
        assert rsp['meta']['pagination']['pages'] == 1
        assert rsp['meta']['pagination']['count'] == 0

    @pytest.mark.django_db
    def test_invalid_view_should_raise_exception(self):
        view_name = 'viewdoesnotexist'
        with pytest.raises(NoReverseMatch):
            reverse(view_name)

    @pytest.mark.parametrize(
        '_model, _camelcase, _view, _view_args, relations',
        [
            ('ExperimentType', 'experiment-types',
             'emgapi_v1:experiment-types',
             [], ['samples', 'runs', 'analyses']),
            # ('Biome', 'biomes', 'emgapi_v1:biomes', ['root'],
            #  ['samples', 'studies']),
            ('Pipeline', 'pipelines', 'emgapi_v1:pipelines', [],
             ['samples', 'studies', 'tools', 'analyses']),
            ('Publication', 'publications', 'emgapi_v1:publications', [],
             ['studies', 'samples']),
            ('Run', 'runs', 'emgapi_v1:runs', [],
             ['pipelines', 'analyses', 'experiment-type', 'sample', 'study',
              'assemblies']),
            ('Assembly', 'assemblies', 'emgapi_v1:assemblies', [],
             ['pipelines', 'analyses', 'runs', 'samples']),
            ('Sample', 'samples', 'emgapi_v1:samples', [],
             ['biome', 'studies', 'runs', 'metadata']),
            ('Study', 'studies', 'emgapi_v1:studies', [],
             ['biomes', 'publications', 'samples', 'downloads',
              'geocoordinates', 'analyses']),
            ('PipelineTool', 'pipeline-tools', 'emgapi_v1:pipeline-tools', [],
             ['pipelines']),
            ('AnalysisJob', 'analysis-jobs', 'emgapi_v1:analyses', [],
             ['go-terms', 'go-slim', 'interpro-identifiers', 'sample',
              'study', 'run', 'assembly', 'downloads', 'taxonomy-ssu',
              'taxonomy-lsu', 'taxonomy']),
        ]
    )
    @pytest.mark.django_db
    def test_list(self, client, _model, _camelcase, _view, _view_args,
                  relations, api_version, run_status):
        model_name = 'emgapi.%s' % _model
        view_name = '%s-list' % _view

        # start from 1
        # https://code.djangoproject.com/ticket/17653
        for pk in range(1, 101):
            if _model in ('Study', 'Sample'):
                _biome = mommy.make('emgapi.Biome', pk=pk)
                _sm = mommy.make('emgapi.Sample',
                                 pk=pk, biome=_biome, is_public=1)
                _st = mommy.make('emgapi.Study', pk=pk, biome=_biome,
                                 is_public=1, samples=[_sm])
                _as = mommy.make('emgapi.AnalysisStatus', pk=3)
                _p = mommy.make('emgapi.Pipeline', pk=1, release_version='1.0')
                mommy.make('emgapi.AnalysisJob', pk=pk, pipeline=_p,
                           analysis_status=_as, run_status_id=4,
                           study=_st, sample=_sm)
            elif _model in ('Run',):
                _biome = mommy.make('emgapi.Biome', pk=pk)
                _sm = mommy.make('emgapi.Sample',
                                 pk=pk, biome=_biome, is_public=1)
                _st = mommy.make('emgapi.Study', pk=pk, biome=_biome,
                                 is_public=1, samples=[_sm])
                mommy.make('emgapi.Run', pk=pk, status_id=run_status,
                           study=_st, sample=_sm)
            elif _model in ('Assembly',):
                _biome = mommy.make('emgapi.Biome', pk=pk)
                _sm = mommy.make('emgapi.Sample',
                                 pk=pk, biome=_biome, is_public=1)
                _st = mommy.make('emgapi.Study', pk=pk, biome=_biome,
                                 is_public=1, samples=[_sm])
                _r = mommy.make('emgapi.Run', pk=pk, status_id=run_status,
                                study=_st, sample=_sm)
                mommy.make('emgapi.Assembly', pk=pk, status_id=run_status,
                           runs=[_r])
            elif _model in ('AnalysisJob',):
                _biome = mommy.make('emgapi.Biome', pk=pk)
                _sm = mommy.make('emgapi.Sample',
                                 pk=pk, biome=_biome, is_public=1)
                _st = mommy.make('emgapi.Study', pk=pk, biome=_biome,
                                 is_public=1, samples=[_sm])
                _r = mommy.make('emgapi.Run', pk=pk, status_id=run_status,
                                study=_st, sample=_sm)
                _as = mommy.make('emgapi.AnalysisStatus', pk=3)
                _p = mommy.make('emgapi.Pipeline', pk=1, release_version='1.0')
                mommy.make('emgapi.AnalysisJob', pk=pk, pipeline=_p,
                           analysis_status=_as, run_status_id=4,
                           study=_st, sample=_sm, run=_r)
            elif _model in ('PipelineTool',):
                _p = mommy.make('emgapi.Pipeline', pk=pk,
                                release_version='1.0')
                _t = mommy.make('emgapi.PipelineTool', pk=pk,
                                tool_name='ToolName')
                mommy.make('emgapi.PipelineReleaseTool', pk=pk,
                           pipeline=_p, tool=_t)
            elif _model in ('Pipeline',):
                mommy.make('emgapi.Pipeline', pk=pk,
                           release_version='1.0')
            # elif _model in ('Biome',):
            #     mommy.make('emgapi.Biome', pk=pk,
            #                biome_name='foo%d' % pk,
            #                lineage='root:foo%d' % pk)
            elif _model in ('Publication',):
                mommy.make('emgapi.Publication', pk=pk,
                           pubmed_id=pk)
            else:
                mommy.make(model_name, pk=pk)

        url = reverse(view_name, args=_view_args)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        # Meta
        assert rsp['meta']['pagination']['page'] == 1
        assert rsp['meta']['pagination']['pages'] == 4
        assert rsp['meta']['pagination']['count'] == 100

        # Links
        host = 'http://testserver/%s' % api_version
        _view_url = _view.split(':')[1]
        first_link = '%s/%s?page=1' % (host, _view_url)
        last_link = '%s/%s?page=4' % (host, _view_url)
        next_link = '%s/%s?page=2' % (host, _view_url)
        assert rsp['links']['first'] == first_link
        assert rsp['links']['last'] == last_link
        assert rsp['links']['next'] == next_link
        assert rsp['links']['prev'] is None

        # Data
        assert len(rsp['data']) == 25

        for d in rsp['data']:
            assert d['type'] == _camelcase
            assert 'attributes' in d
            assert 'relationships' in d
            assert set(d['relationships']) - set(relations) == set()
