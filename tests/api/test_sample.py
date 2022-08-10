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

import pytest

from django.urls import reverse
from model_bakery import baker

from rest_framework import status
from rest_framework.test import APITestCase

from test_utils.emg_fixtures import *  # noqa


@pytest.mark.django_db
class TestSampleAPI(object):

    def test_details(self, client, sample):
        url = reverse("emgapi_v1:samples-detail", args=["ERS01234"])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        # Data
        assert len(rsp) == 1
        assert rsp["data"]["type"] == "samples"
        assert rsp["data"]["id"] == "ERS01234"
        _attr = rsp["data"]["attributes"]
        assert(len(_attr) == 17)
        assert _attr["accession"] == "ERS01234"
        assert _attr["biosample"] == "SAMS01234"
        assert _attr["sample-desc"] == "abcdefghijklmnoprstuvwyz"
        assert _attr["analysis-completed"] == "1970-01-01"
        assert _attr["collection-date"] == "1970-01-01"
        assert _attr["geo-loc-name"] == "Geo Location"
        assert not _attr["environment-biome"]
        assert _attr["environment-feature"] == "abcdef"
        assert _attr["environment-material"] == "abcdef"
        assert _attr["sample-name"] == "Example sample name ERS01234"
        assert _attr["sample-alias"] == "ERS01234"
        assert not _attr["host-tax-id"]
        assert _attr["species"] == "homo sapiense"
        assert _attr["latitude"] == 12.3456
        assert _attr["longitude"] == 456.456

    def test_public(self, client, sample, sample_private):
        url = reverse("emgapi_v1:samples-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        # Meta
        assert rsp["meta"]["pagination"]["page"] == 1
        assert rsp["meta"]["pagination"]["pages"] == 1
        assert rsp["meta"]["pagination"]["count"] == 1

        # Data
        assert len(rsp["data"]) == 1

        d = rsp["data"][0]
        assert d["type"] == "samples"
        assert d["id"] == "ERS01234"
        assert d["attributes"]["accession"] == "ERS01234"


class MockSuccessfulEuropePMCResponse:
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


class MockUnsuccessfulEuropePMCResponse:
    status_code = 404


class TestSampleStudiesPublicationsAnnotationsAPI(APITestCase):

    @mock.patch('emgapi.third_party_metadata.requests.get')
    def test_sample_with_study_with_annotated_pub(self, mock_get):
        biome = baker.make(
            'emgapi.Biome',
            pk=1,
            biome_id=1,
            biome_name='bar',
            lft=0, rgt=1, depth=2,
            lineage='root:ghosts:ectoplasmic',
        )

        sample = baker.make(
            'emgapi.Sample',
            biome=biome,
            pk=1,
            accession='ERS00001',
            primary_accession='SAMS00001',
            is_private=False,
            species='Slimer',
            sample_name='Ectoplasm 1',
            sample_desc='ghostbusters',
            latitude=40.7,
            longitude=74.0,
            last_update='1970-01-01 00:00:00',
            analysis_completed='1970-01-01',
            collection_date='1970-01-01',
            environment_feature='gggbbb',
            environment_material='gggbbb',
            geo_loc_name='New York',
            sample_alias='ERS00001',
        )

        # Sample with no studies
        url = reverse('emgapi_v1:samples-studies-publications-annotations-existence', args=(sample.accession,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertTrue(data['query_possible'])
        self.assertEqual(len(data['study_has_annotations']), 0)

        # Sample with a publicationless study
        study1 = baker.make(
            'emgapi.Study',
            biome=biome,
            study_id=1,
            secondary_accession='SRP0001',
            centre_name='Columbia U',
            is_private=False,
            public_release_date=None,
            study_name='Ghostbusters',
            study_abstract='Present to rescue the planet recurrently',
            study_status='FINISHED',
            data_origination='HARVESTED',
            submission_account_id='User-123',
            result_directory='2017/05/SRP00001',
            last_update='1970-01-01 00:00:00',
            first_created='1970-01-01 00:00:00',
            project_id='PRJDB0001',
        )
        sample.studies.add(study1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertTrue(data['query_possible'])
        self.assertEqual(len(data['study_has_annotations']), 1)
        self.assertFalse(data['study_has_annotations'][study1.accession])

        # Sample with a study with a publication with no annotations
        pub1 = baker.make(
            'emgapi.Publication',
            pk=1,
            pubmed_id='001',
            pub_title='Ghostbusters',
            authors='Venkman, P; Spengler, E; Stantz, R'
        )
        study1.publications.add(pub1)
        mock_get.return_value = MockUnsuccessfulEuropePMCResponse()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertTrue(data['query_possible'])
        self.assertEqual(len(data['study_has_annotations']), 1)
        self.assertFalse(data['study_has_annotations'][study1.accession])

        # Sample with a study with a publication with annotations
        mock_get.return_value = MockSuccessfulEuropePMCResponse()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertTrue(data['query_possible'])
        self.assertEqual(len(data['study_has_annotations']), 1)
        self.assertTrue(data['study_has_annotations'][study1.accession])

        # Sample with a study with multiple pubs
        more_pubs = [
            baker.make(
                'emgapi.Publication',
                pk=pk,
                pubmed_id=pk,
                pub_title=f'{pk} ghosts and a funeral',
                authors='Venkman, P; Spengler, E; Stantz, R'
            )
            for pk in range(2, 5)
        ]
        for pub in more_pubs:
            study1.publications.add(pub)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertTrue(data['query_possible'])
        self.assertEqual(len(data['study_has_annotations']), 1)
        self.assertTrue(all(data['study_has_annotations'].values()))

        # Sample with a study with too many publications for EPMC to query at once
        even_more_pubs = [
            baker.make(
                'emgapi.Publication',
                pk=pk,
                pubmed_id=pk,
                pub_title=f'{pk} ghosts and a funeral',
                authors='Venkman, P; Spengler, E; Stantz, R'
            )
            for pk in range(5, 10)
        ]
        for pub in even_more_pubs:
            study1.publications.add(pub)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertFalse(data['query_possible'])

        # Sample with too many studies to query
        more_studies = [
            baker.make(
                'emgapi.Study',
                biome=biome,
                study_id=pk,
                secondary_accession=f'SRP000{pk}',
                centre_name='Columbia U',
                is_private=False,
                public_release_date=None,
                study_name='Ghostbusters',
                study_abstract='Present to rescue the planet recurrently',
                study_status='FINISHED',
                data_origination='HARVESTED',
                submission_account_id='User-123',
                result_directory='2017/05/SRP00001',
                last_update='1970-01-01 00:00:00',
                first_created='1970-01-01 00:00:00',
                project_id='PRJDB0001',
            )
            for pk in range(2, 10)
        ]
        for study in more_studies:
            sample.studies.add(study)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertFalse(data['query_possible'])


class MockSuccessfulCDCHResponse:
    status_code = 200

    @staticmethod
    def json():
        return {
            'curations': [
                {
                    'attributePost': 'fruit',
                    'valuePost': 'banana',
                    "assertionEvidences": [
                        {
                            "label": "author statement"
                        }
                    ],
                    "updatedTimestamp": "2001-01-00T00:00:00.000+0000",
                }
            ],
            "totalAttributes": 1,
            "totalRecords": 1
        }


class MockUnsuccessfulCDCHResponse:
    status_code = 404


class TestSampleContextualDataClearingHouseMetadataAPI(APITestCase):

    @mock.patch('emgapi.third_party_metadata.requests.get')
    def test_sample_with_study_with_annotated_pub(self, mock_get):
        biome = baker.make(
            'emgapi.Biome',
            pk=1,
            biome_id=1,
            biome_name='bar',
            lft=0, rgt=1, depth=2,
            lineage='root:ghosts:ectoplasmic',
        )

        sample = baker.make(
            'emgapi.Sample',
            biome=biome,
            pk=1,
            accession='ERS00001',
            primary_accession='SAMS00001',
            is_private=False,
            species='Slimer',
            sample_name='Ectoplasm 1',
            sample_desc='ghostbusters',
            latitude=40.7,
            longitude=74.0,
            last_update='1970-01-01 00:00:00',
            analysis_completed='1970-01-01',
            collection_date='1970-01-01',
            environment_feature='gggbbb',
            environment_material='gggbbb',
            geo_loc_name='New York',
            sample_alias='ERS00001',
        )

        # Sample with no additional metadata
        mock_get.return_value = MockUnsuccessfulCDCHResponse()
        url = reverse('emgapi_v1:samples-contextual-data-clearing-house-metadata', args=(sample.accession,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(data, [])

        # Sample with additional metadata
        mock_get.return_value = MockSuccessfulCDCHResponse()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(data, [
            {
                'attributePost': 'fruit',
                'valuePost': 'banana',
                "assertionEvidences": [
                    {
                        "label": "author statement"
                    }
                ],
                "updatedTimestamp": "2001-01-00T00:00:00.000+0000",
            }
        ])
