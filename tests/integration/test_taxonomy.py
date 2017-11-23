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
import os

from django.core.urlresolvers import reverse
from django.core.management import call_command

from rest_framework import status

# import fixtures
from test_utils.emg_fixtures import *  # noqa


@pytest.mark.usefixtures('mongodb')
@pytest.mark.django_db
class TestTaxonomy(object):

    def test_organism_list(self, client, run):
        assert run.accession == 'ABC01234'
        call_command('import_taxonomy', run.accession,
                     os.path.dirname(os.path.abspath(__file__)))

        url = reverse("emgapi:organisms-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp['data']) == 7

        expected = [
            'Flavobacteriaceae', 'Alphaproteobacteria',
            'Cohaesibacter', 'Phyllobacteriaceae', 'Pelagibacteraceae',
            'lwoffii|10', 'Unassigned'
        ]
        ids = [a['attributes']['name'] for a in rsp['data']]
        assert ids == expected

    def test_organisms_tree(self, client, run):
        assert run.accession == 'ABC01234'
        call_command('import_taxonomy', run.accession,
                     os.path.dirname(os.path.abspath(__file__)))

        url = reverse("emgapi:organisms-children-list",
                      args=['Bacteria:Proteobacteria:Alphaproteobacteria'])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp['data']) == 4

        expected = [
            'Bacteria:Proteobacteria:Alphaproteobacteria',
            ('Bacteria:Proteobacteria:Alphaproteobacteria:'
             'Rhizobiales:Cohaesibacteraceae:Cohaesibacter'),
            ('Bacteria:Proteobacteria:Alphaproteobacteria:'
             'Rhizobiales:Phyllobacteriaceae'),
            ('Bacteria:Proteobacteria:Alphaproteobacteria:'
             'Rickettsiales:Pelagibacteraceae')
        ]
        ids = [a['id'] for a in rsp['data']]
        assert ids == expected

    def test_object_does_not_exist(self, client):
        url = reverse("emgapi:organisms-children-list", args=['abc'])
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_empty(self, client, run_emptyresults):
        job = run_emptyresults.accession
        version = run_emptyresults.pipeline.release_version
        assert job == 'EMPTY_ABC01234'

        call_command('import_taxonomy', job,
                     os.path.dirname(os.path.abspath(__file__)))

        url = reverse("emgapi:runs-pipelines-taxonomy-list",
                      args=[job, version])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        assert len(rsp['data']) == 0

    @pytest.mark.parametrize(
        'pipeline_version', [
            {
                'version': '1.0', 'otu': False,
                'endpoint': 'emgapi:runs-pipelines-taxonomy-list',
                'expected': {
                    'taxonomy': {
                         'XanthomonadalesXanthomonadaceae': 2,
                         'Unassigned': 319,
                         'Bacteria': 20,
                         'Proteobacteria': 15,
                         'Alphaproteobacteria': 50,
                         'OPB56': 1,
                         'RhodobacteralesRhodobacteraceae': 42,
                         'Sphingomonadales': 1,
                         'Gammaproteobacteria': 1,
                     }
                 }
            },
            {
                'version': '2.0', 'otu': True,
                'endpoint': 'emgapi:runs-pipelines-taxonomy-list',
                'expected': {
                    'taxonomy': {
                        ('Flavobacteriaceae', 117948): 2,
                        ('Flavobacteriaceae', 117949): 3,
                        ('Unassigned', 578211): 1,
                        ('Unassigned', 0): 158687,
                        ('Bacteria', 674344): 1,
                        ('lwoffii|10', 1097359): 1,
                        ('Alphaproteobacteria', 34419): 2,
                        ('Cohaesibacter', 172411): 1,
                        ('Unassigned', 230083): 1
                    }
                },
            },
            {
                'version': '4.0', 'otu': False,
                'endpoint': 'emgapi:runs-pipelines-taxonomy-ssu',
                'expected': {
                    'taxonomy_ssu': {
                        'Bacteria': 14,
                        'actinobacterium_SCGC_AAA015-M09': 1,
                        'Candidatus_Actinomarina': 5,
                        'Corynebacteriaceae': 3,
                        'Chlamydophryidae': 1,
                        'Phaeocystis': 1,
                        'Prymnesiales': 3,
                        'Chrysochromulina': 2,
                        'Liliopsida': 2,
                    }
                },
            },
            {
                'version': '4.0', 'otu': False,
                'endpoint': 'emgapi:runs-pipelines-taxonomy-lsu',
                'expected': {
                    'taxonomy_lsu': {
                        'Archaea': 2,
                        'Bacteria': 24,
                        'Actinobacteria': 4,
                        'Candidatus_Actinomarina': 4,
                        'Pterocystis': 1,
                        'Nerada_mexicana': 1,
                        'Unassigned': 50,
                        'Viridiplantae': 1,
                        'Chlorophyta': 3,
                    }
                },
            },
        ]
    )
    def test_relations(self, client, analysis_results, pipeline_version):
        version = pipeline_version['version']
        job = analysis_results[version].accession
        endpoint = pipeline_version['endpoint']
        call_command('import_taxonomy', job,
                     os.path.dirname(os.path.abspath(__file__)))

        url = reverse(endpoint, args=[job, version])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        assert len(rsp['data']) == 9

        expected = pipeline_version['expected'][next(iter(
            pipeline_version['expected']))]

        if pipeline_version['otu']:
            ids = {
                (a['attributes']['name'], a['attributes']['otu']):
                    a['attributes']['count']
                for a in rsp['data']
            }
        else:
            ids = {
                a['attributes']['name']: a['attributes']['count']
                for a in rsp['data']
            }
        assert ids == expected

    def test_lineage(self, client, run):
        print(run.__dict__)
        call_command('import_taxonomy', run.accession,
                     os.path.dirname(os.path.abspath(__file__)))

        url = reverse("emgapi:runs-pipelines-taxonomy-list",
                      args=[run.accession, run.pipeline.release_version])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        assert len(rsp['data']) == 9

        expected = {
            (('Bacteria:Bacteroidetes:Flavobacteriia:'
              'Flavobacteriales:Flavobacteriaceae'), 117948): 2,
            (('Bacteria:Bacteroidetes:Flavobacteriia:'
              'Flavobacteriales:Flavobacteriaceae'), 117949): 3,
            ('Unassigned', 578211): 1,
            (('Bacteria:Proteobacteria:Gammaproteobacteria:Pseudomonadales:'
              'Moraxellaceae:Acinetobacter:lwoffii|10'), 1097359): 1,
            ('Bacteria:Proteobacteria:Alphaproteobacteria', 34419): 2,
            (('Bacteria:Proteobacteria:Alphaproteobacteria:'
              'Rhizobiales:Cohaesibacteraceae:Cohaesibacter'), 172411): 1,
            ('Unassigned', 230083): 1,
            (('Bacteria:Proteobacteria:Alphaproteobacteria:'
              'Rickettsiales:Pelagibacteraceae'), 838668): 10,
            (('Bacteria:Proteobacteria:Alphaproteobacteria:'
              'Rhizobiales:Phyllobacteriaceae'), 571263): 1,
        }

        ids = {
            (a['attributes']['lineage'], a['attributes']['otu']):
                a['attributes']['count']
            for a in rsp['data']
        }
        assert ids == expected
