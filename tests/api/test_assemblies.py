#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2021 EMBL - European Bioinformatics Institute
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

from django.urls import reverse

from rest_framework import status

from test_utils.emg_fixtures import *  # noqa


@pytest.mark.django_db
class TestAssembliesAPI:
    def test_asssemblies_list(self, client, assemblies):
        url = reverse("emgapi_v1:assemblies-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp["data"]) == 10

        mock_assemblies_ids = [assembly.id for assembly in assemblies]
        for api_assembly in rsp["data"]:
            assert api_assembly["id"] in mock_assemblies_ids
            assert api_assembly["attributes"]["experiment-type"] == "assembly"

    def test_asssemblies_list(self, client, assemblies, legacy_mapping):
        url = reverse("emgapi_v1:assemblies-detail", args=[legacy_mapping.legacy_accession])
        response = client.get(url)
        assert response.status_code == status.HTTP_301_MOVED_PERMANENTLY
        assert legacy_mapping.new_accession in response.headers["Location"]

    def test_assembly_extra_annotations(self, client, assembly_extra_annotation):
        assembly = assembly_extra_annotation.assembly

        url = reverse("emgapi_v1:assembly-extra-annotations-list", args=[assembly.accession])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp["data"]) == 1
        assert rsp["data"][0]["attributes"]["alias"] == "extra.gff"
