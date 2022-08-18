#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2017-2021 EMBL - European Bioinformatics Institute
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
from django.urls import reverse
from emgapi import models as emg_models
from model_bakery import baker
from rest_framework import status
from test_utils.emg_fixtures import *  # noqa


@pytest.mark.django_db
class TestPermissionsAPI:
    @pytest.fixture(autouse=True)
    def setup_method(self, db, pipelines, experiment_type, analysis_status):
        biome = baker.make("emgapi.Biome", biome_name="foo", lineage="root:foo", pk=123)
        pipeline_v5 = pipelines.filter(release_version="5.0")[0]

        # Webin-000 public
        webin_zero_pub_one = baker.make(
            "emgapi.Study",
            pk=111,
            secondary_accession="SRP0111",
            is_private=False,
            submission_account_id="Webin-000",
            biome=biome,
        )
        webin_zero_pub_two = baker.make(
            "emgapi.Study",
            pk=112,
            secondary_accession="SRP0112",
            is_private=False,
            submission_account_id="Webin-000",
            biome=biome,
        )
        # Webin-000 private
        webin_zero_priv = baker.make(
            "emgapi.Study",
            pk=113,
            secondary_accession="SRP0113",
            is_private=True,
            submission_account_id="Webin-000",
            biome=biome,
        )

        # Webin-111 public
        webin_one_pub = baker.make(
            "emgapi.Study",
            pk=114,
            secondary_accession="SRP0114",
            is_private=False,
            submission_account_id="Webin-111",
            biome=biome,
        )
        # Webin-111 private
        webin_one_priv = baker.make(
            "emgapi.Study",
            pk=115,
            secondary_accession="SRP0115",
            is_private=True,
            submission_account_id="Webin-111",
            biome=biome,
        )

        # unknown public
        baker.make(
            "emgapi.Study",
            pk=120,
            secondary_accession="SRP0120",
            is_private=False,
            submission_account_id=None,
            biome=biome,
        )
        # unknown private
        baker.make(
            "emgapi.Study",
            pk=121,
            secondary_accession="SRP0121",
            is_private=True,
            submission_account_id=None,
            biome=biome,
        )

        # public run (needeed for auth filtering)
        public_run = baker.make(
            "emgapi.Run",
            run_id=1234,
            accession="ABC01234",
            is_private=False,
            experiment_type=experiment_type,
        )

        # private (needeed for auth filtering)
        run_private = baker.make(
            "emgapi.Run",
            run_id=9821,
            accession="ABC01234",
            is_private=True,
            experiment_type=experiment_type,
        )

        # public analyses
        public_id = 1
        # public analyses (ids)
        # - MGYA00000001
        # - MGYA00000002
        # - MGYA00000003
        # AJ Downloads (ids)
        # - id_1
        # - id_2
        # - id_3
        for study in [webin_zero_pub_one, webin_zero_pub_two, webin_one_pub]:
            aj = baker.make(
                "emgapi.AnalysisJob",
                pk=public_id,
                study=study,
                analysis_status=analysis_status,  # 3 - Completed
                is_private=False,
                run=public_run,
                experiment_type=experiment_type,
                pipeline=pipeline_v5,
            )
            baker.make(
                "emgapi.AnalysisJobDownload",
                pk=public_id,
                job=aj,
                pipeline=pipeline_v5,
                alias="id_" + str(public_id),
            )
            public_id += 1

        # private analyses
        private_id = 10
        # private analyses (ids)
        # - MGYA00000010 - Webin-000
        # - MGYA00000011 - Webin-111
        # AJ Downloads (ids)
        # - id_10 - Webin-000
        # - id_11 - Webin-111
        for study in [webin_zero_priv, webin_one_priv]:
            aj = baker.make(
                "emgapi.AnalysisJob",
                pk=private_id,
                study=study,
                analysis_status=analysis_status,  # 3 Completed
                is_private=True,
                run=run_private,
                experiment_type=experiment_type,
                pipeline=pipeline_v5,
            )
            baker.make(
                "emgapi.AnalysisJobDownload",
                pk=private_id,
                job=aj,
                pipeline=pipeline_v5,
                alias="id_" + str(private_id),
            )
            private_id += 1

        # AnalysisJob - public
        # but in a private study (should not be visible)
        # belongs to Webin-000
        baker.make(
            "emgapi.AnalysisJob",
            pk=999,
            study=webin_zero_priv,
            analysis_status=analysis_status,  # 3
            is_private=False,
            run=run_private,
            experiment_type=experiment_type,
            pipeline=pipeline_v5,
        )

    @pytest.mark.parametrize(
        "view, username, count, ids, bad_ids",
        [
            # private
            (
                "emgapi_v1:studies-list",
                "Webin-111",
                5,
                [
                    "MGYS00000111",
                    "MGYS00000112",
                    "MGYS00000114",
                    "MGYS00000115",
                    "MGYS00000120",
                ],
                ["MGYS00000113", "MGYS00000121"],
            ),
            # mydata
            (
                "emgapi_v1:mydata-list",
                "Webin-111",
                2,
                ["MGYS00000114", "MGYS00000115"],
                [],
            ),
            # public
            (
                "emgapi_v1:studies-list",
                None,
                4,
                ["MGYS00000111", "MGYS00000112", "MGYS00000114", "MGYS00000120"],
                ["MGYS00000113", "MGYS00000115", "MGYS00000121"],
            ),
        ],
    )
    def test_list(self, apiclient, view, username, count, ids, bad_ids):
        auth = None
        if username is not None:
            data = {
                "username": username,
                "password": "secret",
            }
            rsp = apiclient.post(
                reverse("obtain_jwt_token_v1"), data=data, format="json"
            )
            token = rsp.json()["data"]["token"]
            auth = "Bearer {}".format(token)

        url = reverse(view)
        if auth is not None:
            response = apiclient.get(url, HTTP_AUTHORIZATION=auth)
        else:
            response = apiclient.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        # Meta
        assert rsp["meta"]["pagination"]["page"] == 1
        assert rsp["meta"]["pagination"]["pages"] == 1
        assert rsp["meta"]["pagination"]["count"] == count

        # Data
        assert len(rsp["data"]) == count
        assert set(ids) - set([d["id"] for d in rsp["data"]]) == set()

        ids.extend(bad_ids)
        assert set(ids) - set([d["id"] for d in rsp["data"]]) == set(bad_ids)

    def test_detail(self, apiclient):
        data = {
            "username": "Webin-000",
            "password": "secret",
        }
        rsp = apiclient.post(reverse("obtain_jwt_token_v1"), data=data, format="json")
        token = rsp.json()["data"]["token"]

        url = reverse("emgapi_v1:studies-detail", args=["SRP0113"])
        response = apiclient.get(url, HTTP_AUTHORIZATION="Bearer {}".format(token))
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        assert rsp["data"]["id"] == "MGYS00000113"

        url = reverse("emgapi_v1:studies-detail", args=["MGYS00000115"])
        response = apiclient.get(url, HTTP_AUTHORIZATION="Bearer {}".format(token))
        assert response.status_code == status.HTTP_404_NOT_FOUND

        url = reverse("emgapi_v1:studies-detail", args=["MGYS00000121"])
        response = apiclient.get(url, HTTP_AUTHORIZATION="Bearer {}".format(token))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        "accession",
        [
            "MGYS00000113",
            "MGYS00000115",
            "MGYS00000121",
            "SRP0113",
            "SRP0115",
            "SRP0121",
        ],
    )
    def test_not_found(self, apiclient, accession):
        url = reverse("emgapi_v1:studies-detail", args=[accession])
        response = apiclient.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_private_analyses(self, apiclient):
        """Test that the analyses list endpoint returns public and
        the private analyses that correspond to a particular user.
        """
        data = {
            "username": "Webin-000",
            "password": "secret",
        }
        rsp = apiclient.post(reverse("obtain_jwt_token_v1"), data=data, format="json")
        token = rsp.json()["data"]["token"]
        auth = "Bearer {}".format(token)

        url = reverse("emgapi_v1:analyses-list")

        response = apiclient.get(url, HTTP_AUTHORIZATION=auth)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        count = 5

        assert response_data["meta"]["pagination"]["page"] == 1
        assert response_data["meta"]["pagination"]["pages"] == 1
        assert response_data["meta"]["pagination"]["count"] == count
        assert len(response_data["data"]) == count
        assert (
            set(
                [
                    "MGYA00000001",
                    "MGYA00000002",
                    "MGYA00000003",
                    "MGYA00000010",
                    "MGYA00000999",  # AJ with tagged as Public but with private Study
                ]
            )
            == set([d["attributes"]["accession"] for d in response_data["data"]])
        )

    def test_private_analyses_anonymous(self, apiclient):
        """Test that the analyses list endpoint is filtering out
        private analyses for anonymous users
        """
        url = reverse("emgapi_v1:analyses-list")
        response = apiclient.get(url)
        assert response.status_code == status.HTTP_200_OK

        rsp = response.json()
        count = 3

        assert rsp["meta"]["pagination"]["page"] == 1
        assert rsp["meta"]["pagination"]["pages"] == 1
        assert rsp["meta"]["pagination"]["count"] == count
        assert len(rsp["data"]) == count
        assert (
            set(
                [
                    "MGYA00000001",
                    "MGYA00000002",
                    "MGYA00000003",
                ]
            )
            == set([d["attributes"]["accession"] for d in rsp["data"]])
        )

    @pytest.mark.parametrize("username", ["Webin-000", "Webin-000", None])
    @pytest.mark.parametrize("analysis", ["MGYA00000001", "MGYA00000002"])
    def test_public_analysis(self, apiclient, username, analysis):
        """Test that anonymous and authenticated users can
        access public analysis.
        """
        auth_token = None
        url = reverse("emgapi_v1:analyses-detail", args=[analysis])
        if username:
            data = {
                "username": username,
                "password": "secret",
            }
            token_response = apiclient.post(
                reverse("obtain_jwt_token_v1"), data=data, format="json"
            )
            token = token_response.json()["data"]["token"]
            auth_token = "Bearer {}".format(token)

        if auth_token:
            response = apiclient.get(url, HTTP_AUTHORIZATION=auth_token)
        else:
            response = apiclient.get(url)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        attributes = response_data["data"]["attributes"]
        assert attributes["analysis-status"] == "3"
        assert attributes["accession"] == analysis
        assert attributes["experiment-type"] == "metagenomic"

    @pytest.mark.parametrize(
        "username,accession_and_expected_status",
        [
            (
                "Webin-000",
                ["MGYA00000010", status.HTTP_200_OK],
            ),
            (
                "Webin-000",
                ["MGYA00000011", status.HTTP_404_NOT_FOUND],
            ),
            (
                "Webin-111",
                ["MGYA00000011", status.HTTP_200_OK],
            ),
            (
                "Webin-111",
                ["MGYA00000010", status.HTTP_404_NOT_FOUND],
            ),
            # anonymous
            (
                None,
                ["MGYA00000011", status.HTTP_404_NOT_FOUND],
            ),
            (
                None,
                ["MGYA00000010", status.HTTP_404_NOT_FOUND],
            ),
        ],
    )
    def test_private_analysis_detail(
        self, apiclient, username, accession_and_expected_status
    ):
        """Test that only authenticated users can their private analysis."""
        analysis, expected_status = accession_and_expected_status
        url = reverse("emgapi_v1:analyses-detail", args=[analysis])

        auth_token = None
        if username:
            data = {
                "username": username,
                "password": "secret",
            }
            token_response = apiclient.post(
                reverse("obtain_jwt_token_v1"), data=data, format="json"
            )
            token = token_response.json()["data"]["token"]
            auth_token = "Bearer {}".format(token)

        if auth_token:
            response = apiclient.get(
                url, args=[analysis], HTTP_AUTHORIZATION=auth_token
            )
        else:
            response = apiclient.get(url)
        assert response.status_code == expected_status

        if expected_status == status.HTTP_200_OK:
            response_data = response.json()
            assert response_data["data"]["attributes"]["accession"] == analysis

    @pytest.mark.parametrize(
        "username_result", [("Webin-000", 1), ("Webin-111", 0), (None, 0)]
    )
    def test_private_analysis_download_list(self, apiclient, username_result):
        """Test that private analysis job download list is avaiable for the users
        that own the analysis
        """
        username, count = username_result
        url = reverse("emgapi_v1:analysisdownload-list", args=["MGYA00000010"])

        if username:
            data = {
                "username": username,
                "password": "secret",
            }
            token_response = apiclient.post(
                reverse("obtain_jwt_token_v1"), data=data, format="json"
            )
            token = token_response.json()["data"]["token"]
            auth_token = "Bearer {}".format(token)

        if username:
            response = apiclient.get(url, HTTP_AUTHORIZATION=auth_token)
        else:
            response = apiclient.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data["meta"]["pagination"]["page"] == 1
        assert response_data["meta"]["pagination"]["pages"] == 1
        assert response_data["meta"]["pagination"]["count"] == count
        assert len(response_data["data"]) == count

    @pytest.mark.parametrize(
        "test_data",
        [
            # username, analysis, analysis_job, expected_response_status
            # privates
            ("Webin-000", "MGYA00000010", "id_10", status.HTTP_200_OK),
            ("Webin-111", "MGYA00000011", "id_11", status.HTTP_200_OK),
            # private - wrong MGYA - AJ download id
            ("Webin-111", "MGYA00000011", "id_10", status.HTTP_404_NOT_FOUND),
            # private - but for a different user
            ("Webin-111", "MGYA00000010", "id_10", status.HTTP_404_NOT_FOUND),
            # public - logged in
            ("Webin-111", "MGYA00000001", "id_1", status.HTTP_200_OK),
            # public - anonymous
            (None, "MGYA00000002", "id_2", status.HTTP_200_OK),
            # private - anonymous
            (None, "MGYA00000010", "id_10", status.HTTP_404_NOT_FOUND),
        ],
    )
    def test_private_analysis_download_detail(self, apiclient, test_data):
        """Test that private analysis job download detail page is avaiable
        for the users that own the analysis (or anyone if public)
        """
        username, aj_accession, ad_id, expected_status = test_data
        url = reverse("emgapi_v1:analysisdownload-detail", args=[aj_accession, ad_id])

        if username:
            data = {
                "username": username,
                "password": "secret",
            }
            token_response = apiclient.post(
                reverse("obtain_jwt_token_v1"), data=data, format="json"
            )
            token = token_response.json()["data"]["token"]
            auth_token = "Bearer {}".format(token)

        if username:
            response = apiclient.get(url, HTTP_AUTHORIZATION=auth_token)
        else:
            response = apiclient.get(url)

        assert response.status_code == expected_status
