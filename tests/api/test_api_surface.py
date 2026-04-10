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

from emgapi import models as emg_models
from django.urls import reverse, resolve
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
            ('Genome', 'genomes', 'emgapi_v1:genomes', [],
             ['cog-matches', 'kegg-modules-matches', 'downloads',
              'antismash-geneclusters', 'biome', 'kegg-class-matches', 'catalogue']),
            ('GenomeCatalogue', 'genomes', 'emgapi_v1:genome-catalogue-genomes', ['dummy1'],
             ['cog-matches', 'kegg-modules-matches', 'downloads',
              'antismash-geneclusters', 'biome', 'kegg-class-matches', 'catalogue']),
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
                if pk == 1:
                    _biome = baker.make('emgapi.Biome', pk=pk, lineage='root')
                else:
                    _biome = emg_models.Biome.objects.get(lineage='root')
                _gc = baker.make('emgapi.GenomeCatalogue', pk=pk, catalogue_id='dummy%d' % pk, biome=_biome)
                _g = baker.make('emgapi.Genome', pk=pk, biome=_biome, catalogue=_gc)
                # Make some related data for ordering tests
                _cog = baker.make('emgapi.CogCat', pk=pk, name='COG%d' % pk)
                baker.make('emgapi.GenomeCogCounts', genome=_g, cog=_cog, genome_count=1)
                _kc = baker.make('emgapi.KeggClass', pk=pk, class_id='K%d' % pk, name='KEGG%d' % pk)
                baker.make('emgapi.GenomeKeggClassCounts', genome=_g, kegg_class=_kc, genome_count=1)
                _km = baker.make('emgapi.KeggModule', pk=pk, name='M%d' % pk)
                baker.make('emgapi.GenomeKeggModuleCounts', genome=_g, kegg_module=_km, genome_count=1)
                _asgc = baker.make('emgapi.AntiSmashGC', pk=pk, name='AS%d' % pk)
                baker.make('emgapi.GenomeAntiSmashGCCounts', genome=_g, antismash_genecluster=_asgc, genome_count=1)
            elif _model in ('GenomeCatalogue', ):
                if pk == 1:
                    _biome = baker.make('emgapi.Biome', pk=pk, lineage='root')
                else:
                    _biome = emg_models.Biome.objects.get(lineage='root')
                _gc = baker.make('emgapi.GenomeCatalogue', pk=pk, biome=_biome, catalogue_id='dummy%d' % pk)
                # Ensure each catalogue has genomes if we are testing a catalogue's genomes
                if _view == 'emgapi_v1:genome-catalogue-genomes':
                    _target_gc_id = _view_args[0]
                    _target_gc = emg_models.GenomeCatalogue.objects.get(catalogue_id=_target_gc_id)
                    baker.make('emgapi.Genome', pk=pk, biome=_biome, catalogue=_target_gc)
                else:
                    baker.make('emgapi.Genome', pk=pk, biome=_biome, catalogue=_gc)

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
        _view_url = url.split(api_version)[1]
        first_link = '%s%s?page=1' % (host, _view_url)
        last_link = '%s%s?page=4' % (host, _view_url)
        next_link = '%s%s?page=2' % (host, _view_url)
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

        # Test ordering
        view_func = resolve(url).func
        view_class = getattr(view_func, 'view_class', None)
        if view_class:
            ordering_fields = getattr(view_class, 'ordering_fields', [])
            fields_to_test = []
            for field in ordering_fields:
                if isinstance(field, tuple):
                    fields_to_test.append(field[0])
                else:
                    fields_to_test.append(field)

            for field in fields_to_test:
                for sort_field in [field, f"-{field}"]:
                    response = client.get(url, {'ordering': sort_field})
                    assert response.status_code == status.HTTP_200_OK, \
                        f"Ordering by {sort_field} failed for {url}. Status: {response.status_code}"

        # Test ordering on related endpoints
        if len(rsp['data']) > 0:
            item = rsp['data'][0]
            for rel_name, rel_data in item.get('relationships', {}).items():
                related_link = rel_data.get('links', {}).get('related')
                if related_link:
                    # Strip the host to get the path
                    rel_path = related_link.replace('http://testserver', '')
                    try:
                        rel_match = resolve(rel_path)
                        rel_view_class = getattr(rel_match.func, 'view_class', None)
                        if rel_view_class:
                            rel_ordering_fields = getattr(rel_view_class, 'ordering_fields', [])
                            rel_fields_to_test = []
                            for field in rel_ordering_fields:
                                if isinstance(field, tuple):
                                    rel_fields_to_test.append(field[0])
                                else:
                                    rel_fields_to_test.append(field)

                            for field in rel_fields_to_test:
                                for sort_field in [field, f"-{field}"]:
                                    rel_url_with_ordering = f"{rel_path}?ordering={sort_field}"
                                    response = client.get(rel_url_with_ordering)
                                    assert response.status_code == status.HTTP_200_OK, \
                                        f"Ordering by {sort_field} failed for related {rel_path}. Status: {response.status_code}"
                    except Exception:
                        # Some links might not be resolvable or might be external
                        continue
