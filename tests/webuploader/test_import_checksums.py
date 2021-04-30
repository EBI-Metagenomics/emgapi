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

import pytest
import os

from django.core.urlresolvers import reverse
from django.core.management import call_command

from rest_framework import status

from model_bakery import baker

import emgapi.models as emg_models

from test_utils.emg_fixtures import *  # noqa


class TestDownloadFileChecksums:
    """Test the import checksums command and API
    """

    @pytest.mark.django_db
    def test_empty_checksums(self, client, pipelines, analysis_results):
        """Assert that analysis with no checksums will return empty values
        """
        fasta_gz, _ = emg_models.FileFormat.objects.get_or_create(format_name="FASTA", compression=True)
        files = [
            ["RNase_P.RF01577.fasta.gz", fasta_gz],
            ["alpha_tmRNA.RF01849.fasta.gz", fasta_gz]
        ]
        a_job = analysis_results["5.0"]
        pipeline = pipelines.filter(release_version="5.0").first()

        for f in files:
            baker.make("emgapi.AnalysisJobDownload",
                       job=a_job,
                       pipeline=pipeline,
                       realname=f[0],
                       alias=f[0],
                       file_format=f[1])

        url = reverse("emgapi_v1:analysisdownload-list", args=[a_job.accession])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        res_files = data["data"]

        returned = {
            rf["id"]: [
                rf["attributes"]["file-format"]["name"],
                rf["attributes"]["file-checksum"]["checksum"],
                rf["attributes"]["file-checksum"]["checksum-algorithm"]] for rf in res_files
        }

        for file_name, file_format in files:
            assert file_name in returned
            assert returned[file_name][0] == file_format.format_name
            assert returned[file_name][1] == ""
            assert returned[file_name][2] == ""

    @pytest.mark.django_db
    def test_import_checksums(self, client, pipelines, analysis_results):
        """Assert that the import worked for genome
        """
        fasta_gz, _ = emg_models.FileFormat.objects.get_or_create(format_name="FASTA", compression=True)
        tsv, _ = emg_models.FileFormat.objects.get_or_create(format_name="TSV", compression=False)
        sha1, _ = emg_models.ChecksumAlgorithm.objects.get_or_create(name="SHA1")

        files = [
            [
                "RNase_P.RF01577.fasta.gz", fasta_gz,
                "8bb47dbe7db5d8af73e3dbcba697d5c8db057460", sha1
            ],
            [
                "alpha_tmRNA.RF01849.fasta.gz", fasta_gz,
                "846dee603b7b8f2f400a6b02558bb9c26938e51f", sha1
            ],
            [
                "beta_tmRNA.RF01850.fasta.gz", fasta_gz,
                "718b7708a1571e64a5ac8848db7ab7497513e8e7", sha1
            ],
            [
                "cyano_tmRNA.RF01851.fasta.gz", fasta_gz,
                "6d6485ce1cbbb0e98ba009d404460bbf85c9f405", sha1
            ],
            [
                "mt-tmRNA.RF02544.fasta.gz", fasta_gz,
                "cf57c9774e9d478547236e4313ecf57ed9ecf2ce", sha1
            ],
            [
                "ERZ1292616_FASTA_LSU.fasta.mseq.tsv", tsv,
                "7298b00129dce6b0986ae74a297bcbba47eee350", sha1
            ]
        ]

        a_job = analysis_results["5.0"]
        pipeline = pipelines.filter(release_version="5.0").first()

        for f in files:
            baker.make("emgapi.AnalysisJobDownload",
                       job=a_job,
                       pipeline=pipeline,
                       realname=f[0],
                       alias=f[0],
                       file_format=f[1])

        call_command("import_checksums", a_job.run.accession,
                     os.path.dirname(os.path.abspath(__file__)),
                     "--pipeline", "5.0")

        url = reverse("emgapi_v1:analysisdownload-list", args=[a_job.accession])
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()["data"]

        returned = {
            rf["id"]: [
                rf["attributes"]["file-checksum"]["checksum"],
                rf["attributes"]["file-checksum"]["checksum-algorithm"]] for rf in response_data
        }

        for f, _, f_hash, f_hash_alg in files:
            assert f in returned
            assert returned[f][0] == f_hash
            assert returned[f][1] == f_hash_alg.name
