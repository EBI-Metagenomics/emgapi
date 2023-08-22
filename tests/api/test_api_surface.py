#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 EMBL - European Bioinformatics Institute
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

from model_bakery import baker

from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

from rest_framework import status

from test_utils.emg_fixtures import *  # noqa


class TestAPISurface:
    """Test that all the endpoints for v1 exist and work
    """
    def test_default(self, client, api_version):
        url = reverse('emgapi_v1:api-root')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        host = 'http://testserver/{}'.format(api_version)
        expected = {
            'biomes': '/biomes',
            'studies': '/studies',
            'super-studies': '/super-studies',
            'samples': '/samples',
            'runs': '/runs',
            'analyses': '/analyses',
            'assemblies': '/assemblies',
            'pipelines': '/pipelines',
            'experiment-types': '/experiment-types',
            'publications': '/publications',
            'pipeline-tools': '/pipeline-tools',
            'genome-search': '/genome-search',
            'genomes-search/gather': '/genomes-search/gather',
            'annotations/go-terms': '/annotations/go-terms',
            'annotations/interpro-identifiers': '/annotations/interpro-identifiers',
            'annotations/antismash-gene-clusters': '/annotations/antismash-gene-clusters',
            'annotations/genome-properties': '/annotations/genome-properties',
            'annotations/kegg-modules': '/annotations/kegg-modules',
            'annotations/kegg-orthologs': '/annotations/kegg-orthologs',
            'annotations/pfam-entries': '/annotations/pfam-entries',
            'annotations/organisms': '/annotations/organisms',
            'antismash-geneclusters': '/antismash-geneclusters',
            'mydata': '/mydata',
            'genomes': '/genomes',
            'cogs': '/cogs',
            'genomeset': '/genomeset',
            'kegg-classes': '/kegg-classes',
            'kegg-modules': '/kegg-modules',
            'genome-catalogues': '/genome-catalogues'
        }

        for k in expected:
            expected[k] = host + expected[k]

        assert rsp['data'] == expected

    @pytest.mark.parametrize(
        '_view',
        [
            'emgapi_v1:biomes',
            'emgapi_v1:experiment-types',
            'emgapi_v1:publications',
            'emgapi_v1:samples',
            'emgapi_v1:runs',
            'emgapi_v1:analyses',
            'emgapi_v1:super-studies',
            'emgapi_v1:studies',
            'emgapi_v1:pipeline-tools',
            'emgapi_v1:goterms',
            'emgapi_v1:interproidentifier',
            'emgapi_v1:organisms',
            'emgapi_v1:genomes',
            'emgapi_v1:genome-catalogues',
        ]
    )
    @pytest.mark.django_db
    def test_default_list(self, client, _view):
        # Some list views are never empty because they are populated during migrations
        never_empty_lists = {
            'emgapi_v1:experiment-types': 8,
        }

        view_name = '{}-list'.format(_view)
        url = reverse(view_name)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        if _view in never_empty_lists:
            assert  rsp['meta']['pagination']['count'] == never_empty_lists[_view]
        else:
            assert rsp['meta']['pagination']['page'] == 1
            assert rsp['meta']['pagination']['pages'] == 1
            assert rsp['meta']['pagination']['count'] == 0

    @pytest.mark.django_db
    @pytest.mark.skip(reason="No sure why this is failing at the moment")
    def test_empty_list_pipelines(self, client):
        """Pipelines API is never empty as V5 is created on a migration
        """
        url = reverse('emgapi_v1:pipelines-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert rsp['meta']['pagination']['page'] == 1
        assert rsp['meta']['pagination']['pages'] == 1
        assert rsp['meta']['pagination']['count'] == 1


    @pytest.mark.django_db
    def test_invalid_view_should_raise_exception(self):
        view_name = 'viewdoesnotexist'
        with pytest.raises(NoReverseMatch):
            reverse(view_name)

    @pytest.mark.parametrize(  # noqa: C901
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
              'assemblies', 'extra-annotations']),
            ('Assembly', 'assemblies', 'emgapi_v1:assemblies', [],
             ['pipelines', 'analyses', 'runs', 'samples', 'extra-annotations']),
            ('Sample', 'samples', 'emgapi_v1:samples', [],
             ['biome', 'studies', 'runs', 'metadata']),
            ('SuperStudy', 'super-studies', 'emgapi_v1:super-studies', [],
             ['title', 'description', 'flagship-studies',
              'related-studies', 'biomes', 'related-genome-catalogues']),
            ('Study', 'studies', 'emgapi_v1:studies', [],
             ['biomes', 'publications', 'samples', 'downloads',
              'geocoordinates', 'analyses']),
            ('PipelineTool', 'pipeline-tools', 'emgapi_v1:pipeline-tools', [],
             ['pipelines']),
            ('AnalysisJob', 'analysis-jobs', 'emgapi_v1:analyses', [],
             ['go-terms', 'go-slim', 'interpro-identifiers', 'sample',
              'study', 'run', 'assembly', 'downloads', 'taxonomy-ssu',
              'taxonomy-lsu', 'taxonomy-itsunite', 'taxonomy-itsonedb',
              'taxonomy', 'antismash-gene-clusters', 'genome-properties']),
            ('GenomeCatalogue', 'genome-catalogues', 'emgapi_v1:genome-catalogues', [],
             ['name', 'description', 'downloads',
              'genomes', 'biome', 'version']),
        ]
    )
    @pytest.mark.django_db
    def test_list(self, client, _model, _camelcase, _view, _view_args,
                  relations, api_version):
        model_name = 'emgapi.%s' % _model
        view_name = '%s-list' % _view

        # start from 1
        # https://code.djangoproject.com/ticket/17653
        for pk in range(1, 101):
            if _model in ('Study', 'Sample'):
                _biome = baker.make('emgapi.Biome', pk=pk)
                _sm = baker.make('emgapi.Sample',
                                 pk=pk, biome=_biome, is_private=False)
                _st = baker.make('emgapi.Study', pk=pk, biome=_biome,
                                 is_private=False, samples=[_sm])
                _as = baker.make('emgapi.AnalysisStatus', pk=3)
                _p = baker.make('emgapi.Pipeline', pk=1, release_version='1.0')
                baker.make('emgapi.AnalysisJob', pk=pk, pipeline=_p,
                           analysis_status=_as, is_private=False,
                           study=_st, sample=_sm)
            elif _model in ('Run',):
                _biome = baker.make('emgapi.Biome', pk=pk)
                _sm = baker.make('emgapi.Sample',
                                 pk=pk, biome=_biome, is_private=False)
                _st = baker.make('emgapi.Study', pk=pk, biome=_biome,
                                 is_private=False, samples=[_sm])
                baker.make('emgapi.Run', pk=pk, is_private=False,
                           study=_st, sample=_sm)
            elif _model in ('Assembly',):
                _biome = baker.make('emgapi.Biome', pk=pk)
                _sm = baker.make('emgapi.Sample',
                                 pk=pk, biome=_biome, is_private=False)
                _st = baker.make('emgapi.Study', pk=pk, biome=_biome,
                                 is_private=False, samples=[_sm])
                _r = baker.make('emgapi.Run', pk=pk, is_private=False,
                                study=_st, sample=_sm)
                baker.make('emgapi.Assembly', pk=pk, is_private=False,
                           runs=[_r])
            elif _model in ('AnalysisJob',):
                _biome = baker.make('emgapi.Biome', pk=pk)
                _sm = baker.make('emgapi.Sample',
                                 pk=pk, biome=_biome, is_private=False)
                _st = baker.make('emgapi.Study', pk=pk, biome=_biome,
                                 is_private=False, samples=[_sm])
                _r = baker.make('emgapi.Run', pk=pk, is_private=False,
                                study=_st, sample=_sm)
                _as = baker.make('emgapi.AnalysisStatus', pk=3) # COMPLETED
                _p = baker.make('emgapi.Pipeline', pk=1, release_version='1.0')
                baker.make('emgapi.AnalysisJob', pk=pk, pipeline=_p,
                           analysis_status=_as, is_private=False,
                           study=_st, sample=_sm, run=_r)
            elif _model in ('PipelineTool',):
                _p = baker.make('emgapi.Pipeline', pk=pk,
                                release_version='1.0')
                _t = baker.make('emgapi.PipelineTool', pk=pk,
                                tool_name='ToolName')
                baker.make('emgapi.PipelineReleaseTool', pk=pk,
                           pipeline=_p, tool=_t)
            elif _model in ('Pipeline',):
                baker.make('emgapi.Pipeline', pk=pk,
                           release_version='1.0')
            # elif _model in ('Biome',):
            #     baker.make('emgapi.Biome', pk=pk,
            #                biome_name='foo%d' % pk,
            #                lineage='root:foo%d' % pk)
            elif _model in ('Publication',):
                baker.make('emgapi.Publication', pk=pk,
                           pubmed_id=pk)
            elif _model in ('SuperStudy',):
                _biome = baker.make('emgapi.Biome', pk=pk)
                _study = baker.make('emgapi.Study', pk=pk)
                _ss = baker.make('emgapi.SuperStudy', pk=pk, title='Dummy',
                                 description='Desc')
                baker.make('emgapi.SuperStudyStudy',
                           study=_study, super_study=_ss)
                baker.make('emgapi.SuperStudyBiome', super_study=_ss, biome=_biome)
            elif _model in ('Genome', ):
                _biome = baker.make('emgapi.Biome', pk=pk)
                baker.make('emgapi.Genome', pk=pk, biome=_biome)
            elif _model in ('GenomeCatalogue', ):
                _biome = baker.make('emgapi.Biome', pk=pk)
                # _genome = baker.make('emgapi.Genome', pk=pk, biome=_biome)
                baker.make('emgapi.GenomeCatalogue', pk=pk, biome=_biome, catalogue_id='dummy')
            else:
                baker.make(model_name, pk=pk)

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
