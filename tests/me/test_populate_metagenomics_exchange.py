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
from unittest import mock

from django.core.management import call_command
from django.utils import timezone

from test_utils.emg_fixtures import *  # noqa

from emgapi.models import AnalysisJob


@pytest.mark.django_db
class TestPopulateMeAPI:
    @pytest.mark.usefixtures("run_multiple_analysis_me")
    def test_population_dry_mode(self, caplog):
        """
        2 of 4 analyses require indexing, both are not in ME API
        1 of 4 needs to be deleted because it was suppressed
        1 was indexed after updated - no action needed
        """
        call_command(
            "populate_metagenomics_exchange",
            dry_run=True,
        )
        assert "Indexing 2 new analyses" in caplog.text
        assert "Dry-mode run: no addition to real ME for MGYA00466090" in caplog.text
        assert "Dry-mode run: no addition to real ME for MGYA00466091" in caplog.text
        assert "Processing 1 analyses to remove" in caplog.text
        assert (
            "MGYA00005678 doesn't exist in the registry, nothing to delete"
            in caplog.text
        )

    @pytest.mark.usefixtures("run_multiple_analysis_me")
    @mock.patch("emgapi.metagenomics_exchange.MetagenomicsExchangeAPI.add_analysis")
    @mock.patch("emgapi.metagenomics_exchange.MetagenomicsExchangeAPI.check_analysis")
    def test_add_new_analysis(self, mock_check_analysis, mock_add_analysis, caplog):
        """
        Test checks new added analysis that was not indexed before, It should be added to ME.
        Post process is mocked.
        AnalysisJob should have updated indexed field and assigned MGX
        """
        pipeline = 4.1
        registry_id = "MGX1"

        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
                self.ok = True

            def json(self):
                return self.json_data

        def mock_check_process(*args, **kwargs):
            if "metadata" in kwargs:
                return None, True
            else:
                return registry_id, True

        mock_add_analysis.return_value = MockResponse({}, 200)
        mock_check_analysis.side_effect = mock_check_process

        call_command(
            "populate_metagenomics_exchange",
            pipeline=pipeline,
        )
        assert "Indexing 1 new analyses" in caplog.text
        assert "Processing 0 analyses to remove" in caplog.text
        assert "Successfully added MGYA00466090" in caplog.text
        ajob = AnalysisJob.objects.filter(pipeline__release_version=pipeline).first()
        assert ajob.last_mgx_indexed
        assert ajob.mgx_accession == registry_id

    @pytest.mark.usefixtures("run_multiple_analysis_me")
    @mock.patch("emgapi.metagenomics_exchange.MetagenomicsExchangeAPI.check_analysis")
    @mock.patch("emgapi.metagenomics_exchange.MetagenomicsExchangeAPI.delete_analysis")
    def test_removals(self, mock_delete_analysis, mock_check_analysis, caplog):
        """
        Test delete process.
        1 analysis should be removed and updated indexed field in DB
        """
        pipeline = 4.0
        mock_check_analysis.return_value = True, True
        mock_delete_analysis.return_value = True

        call_command("populate_metagenomics_exchange", pipeline=pipeline)
        assert "Indexing 0 new analyses" in caplog.text
        assert "Processing 1 analyses to remove" in caplog.text
        assert "Deleting MGYA00005678" in caplog.text
        assert "MGYA00005678 successfully deleted" in caplog.text
        ajob = AnalysisJob.objects.filter(pipeline__release_version=pipeline).first()
        assert ajob.last_mgx_indexed.date() == timezone.now().date()

    @pytest.mark.usefixtures("run_multiple_analysis_me")
    @mock.patch("emgapi.metagenomics_exchange.MetagenomicsExchangeAPI.check_analysis")
    @mock.patch("emgapi.metagenomics_exchange.MetagenomicsExchangeAPI.patch_analysis")
    def test_update(self, mock_patch_analysis, mock_check_analysis, caplog):
        """
        Test update process for job that was indexed before updated.
        MGX accession and last_mgx_indexed should be updated
        """
        pipeline = 5.0
        registry_id = "MGX2"
        mock_check_analysis.return_value = registry_id, False
        mock_patch_analysis.return_value = True
        call_command(
            "populate_metagenomics_exchange",
            pipeline=pipeline,
        )

        assert "Indexing 1 new analyses" in caplog.text
        assert "Processing 0 analyses to remove" in caplog.text
        assert "Patch existing MGYA00466091" in caplog.text
        assert "Analysis MGYA00466091 updated successfully" in caplog.text
        ajob = AnalysisJob.objects.filter(pipeline__release_version=pipeline).first()
        assert ajob.last_mgx_indexed.date() == timezone.now().date()
        assert ajob.mgx_accession == registry_id
