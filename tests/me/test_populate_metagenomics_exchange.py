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


@pytest.mark.django_db
class TestMeAPI:
    @pytest.mark.usefixtures('run_multiple_analysis')
    def test_population_dry_mode(
            self,
            caplog
    ):
        call_command(
            "populate_metagenomics_exchange",
            dev=True,
            dry_run=True,
        )
        assert "Dry-mode run: no addition to real ME for MGYA00001234" in caplog.text
        assert "Dry-mode run: no addition to real ME for MGYA00005678" in caplog.text
        assert "Dry-mode run: no addition to real ME for MGYA00466090" in caplog.text
        assert "Processing 0 analyses to remove" in caplog.text

    @pytest.mark.usefixtures('suppressed_analysis_jobs')
    def test_removals_dry_mode(
            self,
            caplog
    ):
        call_command(
            "populate_metagenomics_exchange",
            dev=True,
            dry_run=True,
        )

        assert "No MGYA00000002 in ME, nothing to delete" in caplog.text
        assert "Processing 0 new analyses" in caplog.text

    @pytest.mark.usefixtures('analysis_existed_in_me')
    def test_update_dry_mode(self, caplog):
        call_command(
            "populate_metagenomics_exchange",
            dev=True,
            dry_run=True,
        )
        assert "Incorrect field None in ME (ERR1806500)" in caplog.text
        assert "Dry-mode run: no patch to real ME for MGYA00147343" in caplog.text
        assert "Processing 0 analyses to remove" in caplog.text
