#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2020 EMBL - European Bioinformatics Institute
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
from unittest.mock import patch

from django.core.management import call_command

from test_utils.emg_fixtures import *  # noqa

from emgapi.models import AnalysisJob, MetagenomicsExchange, ME_Broker

@pytest.mark.django_db
class TestMeAPI:
    @patch("emgapi.metagenomics_exchange.MetagenomicsExchangeAPI.post_request")
    @pytest.mark.usefixtures(
        "me_broker",
        "metagenomics_exchange",
    )
    def test_new_analysis_population(
            self,
            mock_post_request
    ):
        class MockResponse:
            def __init__(self, ok, status_code):
                self.ok = ok
                self.status_code = status_code

        mock_post_request.return_value = MockResponse(True, 201)
        test_run = "ABC01234"
        test_pipeline_version = 5.0
        test_broker = 'EMG'

        call_command(
            "mgx_api",
            run=test_run,
            pipeline=test_pipeline_version,
            broker=test_broker
        )
        analysis = AnalysisJob.objects.filter(run__accession=test_run).filter(pipeline__pipeline_id=test_pipeline_version).first()
        assert ME_Broker.objects.filter(brokerID=test_broker).count() == 1
        broker_id = ME_Broker.objects.filter(brokerID=test_broker).first().id
        assert MetagenomicsExchange.objects.filter(analysis=analysis).filter(broker=broker_id).count() == 1

    @pytest.mark.usefixtures(
        "me_broker",
        "metagenomics_exchange",
    )
    @patch("emgapi.metagenomics_exchange.MetagenomicsExchangeAPI.get_request")
    def test_check_existing_analysis(
            self,
            mock_get_request,
            run_multiple_analysis,
            me_broker,
            metagenomics_exchange,
    ):
        class MockResponse:
            def __init__(self, ok, status_code, json_data):
                self.ok = ok
                self.status_code = status_code
                self.json_data = json_data

            def json(self):
                return self.json_data

        test_run = "ABC01234"
        test_pipeline_version = 1.0
        test_broker = 'MAR'
        analysis = AnalysisJob.objects.filter(run__accession=test_run).filter(
            pipeline__pipeline_id=test_pipeline_version).first()
        json_data = {'datasets': [{'sourceID': analysis.accession}] }
        mock_get_request.return_value = MockResponse(True, 200, json_data)

        call_command(
            "mgx_api",
            run=test_run,
            pipeline=test_pipeline_version,
            broker=test_broker
        )

        assert ME_Broker.objects.filter(brokerID=test_broker).count() == 1
        broker_id = ME_Broker.objects.filter(brokerID=test_broker).first().id
        assert MetagenomicsExchange.objects.filter(analysis=analysis, broker=broker_id).count() == 1
