#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 EMBL - European Bioinformatics Institute
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

from django.urls import reverse
from django.core.management import call_command

from rest_framework import status

from test_utils.emg_fixtures import *  # noqa


@pytest.mark.django_db
class TestContigs:
    """Integration tests for the contigs and it's annotations
    """

    def test_import_contigs(self, client, run_v5):
        """Run an import contigs and check the results
        """
        assert run_v5.accession == 'ABC01234'
        rootpath = os.path.dirname(os.path.abspath(__file__))
        call_command('import_contigs', run_v5.accession, rootpath, '--pipeline', '5.0')

        # list
        list_url = reverse('emgapi_v1:analysis-contigs-list', args=['MGYA00001234'])
        list_response = client.get(list_url)
        assert list_response.status_code == status.HTTP_200_OK
        list_data = list_response.json()
        assert len(list_data['data']) == 3

        # filter with antiSMASH annotations
        list_resp_as = client.get(list_url + '?antismash=biosyntethic')
        assert list_resp_as.status_code == status.HTTP_200_OK
        list_data_as = list_resp_as.json()
        assert len(list_data_as['data']) == 1
        contig_as = list_data_as['data'][0]['attributes']['contig-id']
        assert contig_as == 'ERZ477576.1-NODE-1-length-138181-cov-24.7895'

        # filter with certain PFAM category
        list_resp_pfam = client.get(list_url + '?pfam=PF00011')
        assert list_resp_pfam.status_code == status.HTTP_200_OK
        list_data_pfam = list_resp_pfam.json()
        assert len(list_data_pfam['data']) == 1
        contig_pfam = list_data_pfam['data'][0]['attributes']['contig-id']
        assert contig_pfam == 'ERZ477576.2-NODE-2-length-89330-cov-17.4389'

        # expect no results
        list_resp_empty = client.get(list_url + '?go=XXXXXX')
        assert list_resp_empty.status_code == status.HTTP_200_OK
        len(list_resp_empty.json()['data']) == 0
