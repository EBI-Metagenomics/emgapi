#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2017-2022 EMBL - European Bioinformatics Institute
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

from unittest.mock import patch

from django.urls import reverse
from django.core.management import call_command
from emgapi.models import Run

from test_utils.emg_fixtures import *  # noqa


@pytest.mark.django_db
class TestSyncENAStudies:
    @patch("emgena.models.Run.objects")
    def test_make_runs_private(self, ena_run_objs_mock, ena_private_runs):
        ena_run_objs_mock.using("era_pro").filter.return_value = ena_private_runs

        public_runs = Run.objects.order_by("?").all()[0:5]

        for run in public_runs:
            run.is_private = False

        Run.objects.bulk_update(public_runs, ["is_private"])

        call_command("sync_runs_with_ena")

        for run in public_runs:
            run.refresh_from_db()
            assert run.is_private == True

    @patch("emgena.models.Run.objects")
    def test_make_runs_public(self, ena_run_objs_mock, ena_public_runs):
        ena_run_objs_mock.using("era_pro").filter.return_value = ena_public_runs

        private_runs = Run.objects.order_by("?").all()[0:5]

        for run in private_runs:
            run.is_private = True

        Run.objects.bulk_update(private_runs, ["is_private"])

        call_command("sync_runs_with_ena")

        for run in private_runs:
            run.refresh_from_db()
            assert run.is_private == False

    @patch("emgena.models.Run.objects")
    def test_suppress_studies(self, ena_run_objs_mock, ena_suppressed_runs):
        ena_run_objs_mock.using("era_pro").filter.return_value = ena_suppressed_runs

        suppress_runs = Run.objects.order_by("?").all()[0:5]

        for run in suppress_runs:
            run.is_suppressed = False
            run.suppression_reason = None
            run.unsuppress(save=True)

        call_command("sync_runs_with_ena")

        for run in suppress_runs:
            run.refresh_from_db()
            assert run.is_suppressed == True
            ena_run = next(
                e
                for e in ena_suppressed_runs
                if e.run_id == run.accession
            )
            assert (
                ena_run.get_status_id_display().lower()
                == run.get_suppression_reason_display().lower()
            )
