#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2017-2021 EMBL - European Bioinformatics Institute
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

import random

import pytest
from django.core.urlresolvers import reverse
from emgapianns import models as m_models
from rest_framework import status
from test_utils.emg_fixtures import *  # noqa


@pytest.fixture()
def contigs():
    contigs = []
    for i in range(0, 30):
        contig = m_models.AnalysisJobContig(
            contig_id=str(i),
            length=random.randint(500, 10000),
            coverage=random.randint(10, 100),
            analysis_id=1234,
            accession="MGYA00001234",
            job_id=1234,
            pipeline_version="5.0",
        )
        contig.cogs.append(
            m_models.AnalysisJobCOGAnnotation(
                cog=random.choice(["A", "B", "C"]), count=random.randint(1, 100)
            )
        )
        contig.has_cog = True

        contig.gos.append(
            m_models.AnalysisJobGoTermAnnotation(
                go_term=random.choice(["GO01", "GO02", "GO03"]),
                count=random.randint(1, 100),
            )
        )
        contig.has_go = True
        contigs.append(contig)

    m_models.AnalysisJobContig.objects.insert(contigs)


@pytest.mark.usefixtures("mongodb")
@pytest.mark.django_db
class TestContigsAPI:
    def test_contigs(self, client, contigs, run_v5):
        """Contigs endpoint pagination test"""

        assert run_v5.accession == "ABC01234"

        list_url = reverse("emgapi_v1:analysis-contigs-list", args=["MGYA00001234"])

        list_response = client.get(list_url)

        assert list_response.status_code == status.HTTP_200_OK

        list_data = list_response.json()

        assert list_data["meta"] == {"pagination": {"count": 30}}
        assert len(list_data["links"]["next"]) != 0
        assert list_data["links"]["prev"] is None
        assert len(list_data["data"]) == 25

        next_page = list_data["links"]["next"]
        next_response = client.get(next_page)
        assert next_response.status_code == status.HTTP_200_OK

        next_data = next_response.json()
        assert next_data["meta"] == {"pagination": {"count": 30}}
        assert next_data["links"]["next"] is None
        assert len(next_data["links"]["prev"]) != 0
        assert len(next_data["data"]) == 5

    def test_contigs_filtered(self, client, contigs, run_v5):
        """Contigs endpoint filter test"""

        assert run_v5.accession == "ABC01234"

        list_url = reverse("emgapi_v1:analysis-contigs-list", args=["MGYA00001234"])

        filtered_contigs = m_models.AnalysisJobContig.objects.filter(
            analysis_id=1234, gos__go_term="GO01"
        )[:25]

        # filter with GO01 annotations
        filtered_response = client.get(list_url + "?go=GO01")

        assert filtered_response.status_code == status.HTTP_200_OK

        filterd_data = filtered_response.json()
        assert len(filterd_data["data"]) == len(filtered_contigs)

        for contig in filterd_data["data"]:
            contig_id = contig["attributes"]["contig-id"]
            has_cog = contig["attributes"]["has-cog"]
            db_contig = next(fc for fc in filtered_contigs if fc.contig_id == contig_id)
            assert contig_id == db_contig.contig_id
            assert has_cog == db_contig.has_cog
