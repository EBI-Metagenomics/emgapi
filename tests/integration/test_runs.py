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


# import pytest

from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from model_mommy import mommy

from emgapi.models import Run  # noqa


class TestRunAPI(APITestCase):

    def test_public(self):
        _as = mommy.make('emgapi.AnalysisStatus', pk=3)
        _p = mommy.make('emgapi.Pipeline', pk=1, release_version="1.0")
        _r1 = mommy.make("emgapi.AnalysisJob", pk=123, accession="123",
                         pipeline=_p, analysis_status=_as, run_status_id=4)
        _r2 = mommy.make("emgapi.AnalysisJob", pk=456, accession="456",
                         pipeline=_p, run_status_id=2)
        mommy.make("emgapi.Sample", pk=123, accession="123",
                   analysis=[_r1], is_public=1)
        mommy.make("emgapi.Sample", pk=456, accession="456",
                   analysis=[_r2], is_public=0)

        url = reverse("emgapi:samples-list")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        # Meta
        assert rsp['meta']['pagination']['page'] == 1
        assert rsp['meta']['pagination']['pages'] == 1
        assert rsp['meta']['pagination']['count'] == 1

        # Data
        assert len(rsp['data']) == 1

        for d in rsp['data']:
            assert d['type'] == "samples"
            assert d['id'] == "123"
