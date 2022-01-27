#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
from unittest import mock

from django.urls import reverse
from model_bakery import baker

from rest_framework import status
from rest_framework.test import APITestCase


class MockEuropePMCResponse:
    status_code = 200

    @staticmethod
    def json():
        return [
            {
                'annotations': [
                    {
                        'prefix': 'Love is required whenever he’s ',
                        'exact': 'sequenced',
                        'postfix': '. It comes just before the assembly.',
                        'type': 'LS',
                    }
                ]
            }
        ]


class TestPublicationAPI(APITestCase):
    def setUp(self):
        baker.make(
            'emgapi.Publication',
            pk=7,
            pubmed_id='007',
            pub_title='The man with the golden metagenome',
            authors='Bond, J; Moneypenny, J; et al'
        )

    def test_default(self):
        url = reverse('emgapi_v1:publications-list')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

    @mock.patch('emgapi.europe_pmc.requests.get')
    def test_europe_pmc_annotations(self, mock_get):
        mock_get.return_value = MockEuropePMCResponse()
        url = reverse('emgapi_v1:publications-europe-pmc-annotations', args=('007',))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        annotations = response.json()
        self.assertIn('sample_processing', annotations['data'])
        first_group = annotations['data']['sample_processing'][0]
        self.assertEqual(first_group['title'], 'Library strategy')
        self.assertEqual(len(first_group['annotations']), 1)
