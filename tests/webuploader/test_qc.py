#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

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

import pytest
import os

from django.urls import reverse
from django.core.management import call_command

from rest_framework import status

from test_utils.emg_fixtures import *  # noqa


@pytest.mark.django_db
class TestCLI:
    def test_qc(self, client, run):
        call_command(
            "import_qc",
            "ABC01234",
            os.path.dirname(os.path.abspath(__file__)),
            pipeline="4.1",
        )

        url = reverse("emgapi_v1:analyses-detail", args=["MGYA00001234"])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp["data"]["attributes"]["analysis-summary"]) == 5

        expected = [
            {"key": "Submitted nucleotide sequences", "value": "12345"},
            {
                "key": "Nucleotide sequences after format-specific filtering",
                "value": "12345",
            },
            {"key": "Predicted CDS", "value": "12345"},
            {"key": "Predicted CDS with InterProScan match", "value": "12345"},
            {"key": "Total InterProScan matches", "value": "12345678"},
        ]

        summary = rsp["data"]["attributes"]["analysis-summary"]
        summary.sort(key=lambda i: i["key"])
        expected.sort(key=lambda i: i["key"])
        assert summary == expected

    @pytest.mark.parametrize(
        "results",
        (
            {
                "pipeline": "1.0",
                "accession": "MGYA00001234",
                "expected": [
                    {"key": "Submitted nucleotide sequences", "value": "12345"},
                    {
                        "key": (
                            "Nucleotide sequences after format-specific " "filtering"
                        ),
                        "value": "12345",
                    },
                    {"key": "Total InterProScan matches", "value": "12345678"},
                    {"key": "Predicted CDS with InterProScan match", "value": "12345"},
                    {"key": "Predicted CDS", "value": "12345"},
                ],
            },
            {
                "pipeline": "4.0",
                "accession": "MGYA00005678",
                "expected": [
                    {"key": "Submitted nucleotide sequences", "value": "54321"},
                    {
                        "key": (
                            "Nucleotide sequences after format-specific " "filtering"
                        ),
                        "value": "54321",
                    },
                    {"key": "Total InterProScan matches", "value": "87654321"},
                    {"key": "Predicted CDS with InterProScan match", "value": "54321"},
                    {"key": "Predicted CDS", "value": "54321"},
                ],
            },
            {
                "pipeline": "5.0",
                "accession": "MGYA00466090",
                "expected": [
                    {"key": "Submitted nucleotide sequences", "value": "6060"},
                    {
                        "key": "Nucleotide sequences after format-specific filtering",
                        "value": "6060",
                    },
                    {
                        "key": "Nucleotide sequences after length filtering",
                        "value": "6060",
                    },
                    {
                        "key": "Nucleotide sequences after undetermined bases filtering",
                        "value": "6060",
                    },
                    {"key": "Total InterProScan matches", "value": "50732"},
                    {"key": "Predicted CDS with InterProScan match", "value": "13914"},
                    {"key": "Contigs with InterProScan match", "value": "5445"},
                    {"key": "Predicted CDS", "value": "19783"},
                    {"key": "Contigs with predicted CDS", "value": "6043"},
                    {"key": "Contigs with predicted RNA", "value": "152"},
                    {"key": "Predicted SSU sequences", "value": "7"},
                    {"key": "Predicted LSU sequences", "value": "12"},
                ],
            },
        ),
    )
    @pytest.mark.usefixtures("analysis_metadata_variable_names")
    def test_qc_multiple_pipelines(self, client, run_multiple_analysis, results):
        call_command(
            "import_qc",
            "ABC01234",
            os.path.dirname(os.path.abspath(__file__)),
            pipeline="1.0",
        )
        call_command(
            "import_qc",
            "ABC01234",
            os.path.dirname(os.path.abspath(__file__)),
            pipeline="4.0",
        )
        call_command(
            "import_qc",
            "ABC01234",
            os.path.dirname(os.path.abspath(__file__)),
            pipeline="5.0",
        )
        # call_command(
        #     "import_analysis_summaries",
        #     "1"
        # )

        url = reverse("emgapi_v1:analyses-detail", args=[results["accession"]])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        if results["pipeline"] == "5.0":
            temp = rsp["data"]["attributes"]["analysis-summary"]
            # ouput temp
            logging.debug('temp')
            logging.debug(temp)


            # print results
            assert len(rsp["data"]["attributes"]["analysis-summary"]) == 12

        else:
            assert len(rsp["data"]["attributes"]["analysis-summary"]) == 5

        expected = results["expected"]
        # assert rsp["data"]["attributes"]["analysis-summary"] == expected

    def test_empty_qc(self, client, run_emptyresults):
        run = run_emptyresults.run.accession
        job = run_emptyresults.accession
        version = run_emptyresults.pipeline.release_version
        assert run == "ABC01234"
        call_command(
            "import_qc",
            job,
            os.path.dirname(os.path.abspath(__file__)),
            pipeline=version,
        )

        url = reverse("emgapi_v1:analyses-detail", args=[job])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp["data"]["attributes"]["analysis-summary"]) == 0
