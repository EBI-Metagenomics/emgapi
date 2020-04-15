#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2020 EMBL - European Bioinformatics Institute
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
import os

from django.core.urlresolvers import reverse
from django.core.management import call_command

from rest_framework import status

from test_utils.emg_fixtures import *  # noqa


@pytest.mark.usefixtures('mongodb')
@pytest.mark.django_db
class TestAnnotations:

    @property
    def _annotation_endpoints(self):
        return [
            ['emgapi_v1:analysis-goslim-list', 'go_slim'], 
            ['emgapi_v1:analysis-goterms-list', 'go'],
            ['emgapi_v1:analysis-interpro-list', 'interpro'],
            ['emgapi_v1:analysis-genome-properties-list', 'genome_properties'],
            ['emgapi_v1:analysis-kegg-orthologs-list', 'kegg'],
            ['emgapi_v1:analysis-pfam-entries-list', 'pfam'],
            ['emgapi_v1:analysis-kegg-modules-list', 'kegg-module'],
            ['emgapi_v1:analysis-antismash-gene-clusters-list', 'antismash']
        ]

    @property
    def _import_suffixes(self):
        return ['.ipr', '.go', '.go_slim',
                '.kegg_pathways', '.pfam', '.ko',
                '.gprops', '.antismash']

    def test_goslim(self, client, run):
        """Test GO Slim list and detail"""
        assert run.accession == 'ABC01234'
        call_command('import_summary', run.accession,
                     os.path.dirname(os.path.abspath(__file__)),
                     suffix='.go_slim')

        url = reverse('emgapi_v1:goterms-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp['data']) == 3

        expected = ['GO:0030246', 'GO:0046906', 'GO:0043167']
        ids = [a['id'] for a in rsp['data']]
        assert ids.sort() == expected.sort()

        url = reverse('emgapi_v1:goterms-detail', args=['GO:0030246'])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert rsp['data']['id'] == 'GO:0030246'

    def test_go(self, client, run):
        """Test GO list and detail"""
        assert run.accession == 'ABC01234'
        call_command('import_summary', run.accession,
                     os.path.dirname(os.path.abspath(__file__)),
                     suffix='.go')

        url = reverse('emgapi_v1:goterms-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp['data']) == 6

        expected = ['GO:0030170', 'GO:0019842', 'GO:0030246',
                    'GO:0046906', 'GO:0043167', 'GO:0005515']
        ids = [a['id'] for a in rsp['data']]
        assert ids.sort() == expected.sort()

        url = reverse('emgapi_v1:goterms-detail', args=['GO:0030170'])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert rsp['data']['id'] == 'GO:0030170'

    def test_ipr(self, client, run):
        """Test IPR list and detail"""
        assert run.accession == 'ABC01234'
        call_command('import_summary', run.accession,
                     os.path.dirname(os.path.abspath(__file__)),
                     suffix='.ipr')

        url = reverse('emgapi_v1:interproidentifier-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp['data']) == 6

        expected = ['IPR009739', 'IPR021425', 'IPR021710',
                    'IPR033771', 'IPR024561', 'IPR013698']
        ids = [a['id'] for a in rsp['data']]
        assert ids.sort() == expected.sort()

        url = reverse('emgapi_v1:interproidentifier-detail',
                      args=['IPR009739'])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert rsp['data']['id'] == 'IPR009739'

    def test_object_does_not_exist(self, client):
        """Test results for an existent annotation"""
        url = reverse('emgapi_v1:goterms-detail', args=['GO:9999'])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        url = reverse('emgapi_v1:interproidentifier-detail', args=['IPR9999'])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_empty(self, client, run_emptyresults):
        """Test empty annotations"""
        assert run_emptyresults.release_version == '4.1'
        assert run_emptyresults.accession == 'MGYA00001234'

        accession = run_emptyresults.accession

        for suffix in self._import_suffixes:
            call_command('import_summary', accession,
                         os.path.dirname(os.path.abspath(__file__)),
                         pipeline=run_emptyresults.release_version,
                         suffix=suffix)

        for endpoint, _ in self._annotation_endpoints:
            url = reverse('emgapi_v1:analysis-goslim-list', args=[accession])
            response = client.get(url)
            assert response.status_code == status.HTTP_200_OK
            rsp = response.json()
            assert len(rsp['data']) == 0

    @pytest.mark.parametrize('expected', [{
        'data': {
            'M00003': {
                'completeness': 100.0,
                'name': 'Gluconeogenesis, oxaloacetate => fructose-6P',
                'description': 'Pathway modules; Carbohydrate metabolism; Central carbohydrate metabolism',
                'matching-kos': ['K01610', 'K01803', 'K15633', 'K01689', 'K00927', 'K00134', 'K01834', 'K03841', 'K01623', 'K01624'],
                'missing-kos': []
            },
            'M00005': {
                'completeness': 100.0,
                'name': 'PRPP biosynthesis, ribose 5P => PRPP',
                'description': 'Pathway modules; Carbohydrate metabolism; Central carbohydrate metabolism',
                'matching-kos': ['K00948'],
                'missing-kos': []
            },
            'M00010': {
                'completeness': 100.0,
                'name': 'Citrate cycle, first carbon oxidation, oxaloacetate => 2-oxoglutarate',
                'description': 'Pathway modules; Carbohydrate metabolism; Central carbohydrate metabolism',
                'matching-kos': ['K00031', 'K01647', 'K01681', 'K00030'],
                'missing-kos': []
            },
            'M00015': {
                'completeness': 99.0,
                'name': 'Proline biosynthesis, glutamate => proline',
                'description': 'Pathway modules; Amino acid metabolism; Arginine and proline metabolism',
                'matching-kos': ['K00147', 'K00286', 'K00931'],
                'missing-kos': ['K00001']
            }
        }
    }])
    @pytest.mark.parametrize('pipeline_version', ['5.0'])
    def test_kegg_modules(self, client, analysis_results, pipeline_version, expected):
        """Test the import_summary for KEGG modules
        """
        run = analysis_results[pipeline_version].run
        job = analysis_results[pipeline_version]

        call_command('import_summary', run.accession,
                     os.path.dirname(os.path.abspath(__file__)),
                     pipeline='5.0',
                     suffix='.paths.kegg')

        url = reverse('emgapi_v1:analysis-kegg-modules-list', args=[job.accession])
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK

        rsp = response.json()
        for entry in rsp['data']:
            attributes = entry['attributes']
            accession = attributes['accession']
            for key, value in expected['data'][accession].items():
                assert attributes[key] == value

            detail_url = reverse('emgapi_v1:keggmodules-detail', args=[accession])
            detail_resp = client.get(detail_url)
            assert detail_resp.status_code == status.HTTP_200_OK
            detail_data = detail_resp.json()
            assert detail_data['data']['attributes']['accession'] == accession
            for key in detail_data['data']['attributes'].keys():
                if key != 'accession':
                    assert detail_data['data']['attributes'][key] == expected['data'][accession][key]

    @pytest.mark.parametrize('expected', [{
        'data': {
            'GenProp0001': ['Chorismate biosynthesis via shikimate', 'Yes'],
            'GenProp0002': ['Coenzyme F420 utilization', 'Partial'],
            'GenProp0010': ['Inteins', 'No'],
            'GenProp0021': ['CRISPR region', 'Yes']
        }
    }])
    @pytest.mark.parametrize('pipeline_version', ['5.0'])
    def test_genome_properties(self, client, analysis_results, pipeline_version, expected):
        """Test the import_summary for Genome Properties
        """
        run = analysis_results[pipeline_version].run
        job = analysis_results[pipeline_version]

        call_command('import_summary', run.accession,
                     os.path.dirname(os.path.abspath(__file__)),
                     pipeline='5.0',
                     suffix='.paths.gprops')

        url = reverse('emgapi_v1:analysis-genome-properties-list', args=[job.accession])
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK

        rsp = response.json()
        for entry in rsp['data']:
            attributes = entry['attributes']
            accession = attributes['accession']
            assert attributes['presence'] == expected['data'][accession][1]

            detail_url = reverse('emgapi_v1:genome-properties-detail', args=[accession])
            detail_resp = client.get(detail_url)
            assert detail_resp.status_code == status.HTTP_200_OK
            detail_data = detail_resp.json()

            attrs = detail_data['data']['attributes']
            assert attrs['accession'] in expected['data']
            assert attrs['description'] == expected['data'][accession][0]

    @pytest.mark.parametrize('expected', [{
        'data': {
            'terpene': [62, 'Terpene'],
            'bacteriocin': [11, 'Bacteriocin or other unspecified ' + 
                                'ribosomally synthesised and post-translationally ' + 
                                'modified peptide product (RiPP) cluster'],
            'arylpolyene': [3, 'Aryl polyene cluster'],
            't3pks': [1, 'Type III PKS']
        }
    }])
    @pytest.mark.parametrize('pipeline_version', ['5.0'])
    def test_antismash(self, client, analysis_results, pipeline_version, expected):
        """Test the import_summary for antiSMASH
        """
        run = analysis_results[pipeline_version].run
        job = analysis_results[pipeline_version]

        call_command('import_summary', run.accession,
                     os.path.dirname(os.path.abspath(__file__)),
                     pipeline='5.0',
                     suffix='.antismash')

        url = reverse('emgapi_v1:analysis-antismash-gene-clusters-list',
                      args=[job.accession])
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK

        rsp = response.json()
        for entry in rsp['data']:
            attributes = entry['attributes']
            accession = attributes['accession']
            assert attributes['count'] == expected['data'][accession][0]

            detail_url = reverse('emgapi_v1:antismash-gene-clusters-detail', args=[accession])
            detail_resp = client.get(detail_url)
            assert detail_resp.status_code == status.HTTP_200_OK
            detail_data = detail_resp.json()
            assert detail_data['data']['attributes']['accession'] in expected['data']
            assert detail_data['data']['attributes']['description'] == expected['data'][accession][1]

    @pytest.mark.parametrize(
        'pipeline_version_data', [
            {'version': '1.0', 'expected': {
                'go_slim': {
                    'GO:0030246': 23011, 'GO:0043167': 3222011,
                    'GO:0046906': 232611
                },
                'go_terms': {
                    'GO:0005515': 6016, 'GO:0019842': 1377,
                    'GO:0030170': 2885, 'GO:0030246': 230,
                    'GO:0043167': 32220, 'GO:0046906': 2326
                },
                'interpro': {
                    'IPR009739': 1, 'IPR013698': 6, 'IPR021425': 2,
                    'IPR021710': 3, 'IPR024561': 5, 'IPR033771': 4
                },
            }},
            {'version': '4.0', 'expected': {
                'go_slim': {
                    'GO:0005618': 1222, 'GO:0009276': 0,
                    'GO:0016020': 1414622
                },
                'go_terms': {
                    'GO:0005575': 67, 'GO:0005576': 37, 'GO:0005618': 12,
                    'GO:0009276': 0, 'GO:0016020': 14146, 'GO:0019867': 504
                },
                'interpro': {
                    'IPR006677': 3, 'IPR010326': 1, 'IPR011459': 6,
                    'IPR023385': 5, 'IPR024548': 2, 'IPR031692': 4
                },
            }},
            {'version': '5.0', 'expected': {
                'go_slim': {
                    'GO:0005618': 392, 'GO:0009276': 10,
                    'GO:0016020': 45671, 'GO:1904659': 101,
                },
                'go_terms': {
                    'GO:0005575': 77, 'GO:0005576': 37, 'GO:0009276': 1, 
                    'GO:0019868': 256, 'GO:0005618': 23,
                },
                'interpro': {
                    'IPR006677': 3, 'IPR010326': 1, 'IPR011459': 6,
                    'IPR023385': 5, 'IPR024548': 2, 'IPR031692': 4
                },
                'genome_properties': {
                    'GenProp0001': 'Yes', 'GenProp0002': 'Partial',
                    'GenProp0010': 'No', 'GenProp0021': 'Yes'
                },
                'kegg': {
                    'K00003': 42, 'K00005': 3, 'K00009': 3,
                    'K00010': 13, 'K00012': 26, 'K00013': 15
                },
                'pfam': {
                    'PF00002': 1, 'PF00003': 1, 'PF00004': 1092,
                    'PF00005': 9539
                },
                'antismash': {
                    'terpene': 62,
                    'bacteriocin': 11,
                    'arylpolyene': 3,
                    't3pks': 1
                },
                'kegg_module': {
                    'M00003': 100.0,
                    'M00005': 100.0,
                    'M00010': 100.0,
                    'M00015': 99.0
                }
            }}
        ]
    )
    def test_relations(self, client, analysis_results, pipeline_version_data):
        """Test the import summary command and the API results
        """
        version = pipeline_version_data['version']
        run = analysis_results[version].run
        job = analysis_results[version]

        for suffix in self._import_suffixes:
            call_command('import_summary', run.accession,
                         os.path.dirname(os.path.abspath(__file__)),
                         pipeline=version,
                         suffix=suffix)

        for endpoint, prop in self._annotation_endpoints:
            url = reverse(endpoint, args=[job.accession])
            response = client.get(url)
            assert response.status_code == status.HTTP_200_OK
            rsp = response.json()
            if prop in pipeline_version_data['expected']:
                expected = pipeline_version_data['expected'][prop]
                assert len(rsp['data']) == len(expected)
                field = 'count'
                if prop == 'kegg_modules':
                    field = 'completeness'
                elif prop == 'genome_properties':
                    field = 'presence'
                ids = {
                    a['attributes']['accession']: a['attributes'][field]
                    for a in rsp['data']
                }
                assert ids == expected
