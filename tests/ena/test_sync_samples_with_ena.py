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
from emgapi.models import Sample, Assembly, AnalysisJob, Run

from test_utils.emg_fixtures import *  # noqa


@pytest.mark.django_db
class TestSyncENAStudies:
    @patch("emgena.models.Sample.objects")
    def test_make_samples_private(self, ena_sample_objs_mock, ena_private_samples):
        ena_sample_objs_mock.using("era").filter.return_value = ena_private_samples

        public_samples = Sample.objects.order_by("?").all()[0:5]

        for sample in public_samples:
            sample.is_private = False

        Sample.objects.bulk_update(public_samples, ["is_private"])

        call_command("sync_samples_with_ena")

        for sample in public_samples:
            sample.refresh_from_db()
            assert sample.is_private == True


    @patch("emgena.models.Sample.objects")
    def test_make_samples_public(self, ena_sample_objs_mock, ena_public_samples):
        ena_sample_objs_mock.using("era").filter.return_value = ena_public_samples

        private_samples = Sample.objects.order_by("?").all()[0:5]

        for sample in private_samples:
            sample.is_private = True

        Sample.objects.bulk_update(private_samples, ["is_private"])

        call_command("sync_samples_with_ena")

        for sample in private_samples:
            sample.refresh_from_db()
            assert sample.is_private == False


    @patch("emgena.models.Sample.objects")
    def test_suppress_samples(self, ena_sample_objs_mock, ena_suppressed_samples):
        ena_sample_objs_mock.using("era").filter.return_value = ena_suppressed_samples

        suppressed_samples = Sample.objects.order_by("?").all()[0:5]

        for sample in suppressed_samples:
            sample.is_suppressed = False
            sample.suppression_reason = None
            sample.unsuppress(save=True)

        call_command("sync_samples_with_ena")

        for sample in suppressed_samples:
            sample.refresh_from_db()
            assert sample.is_suppressed == True
            ena_sample = next(
                e
                for e in ena_suppressed_samples
                if e.sample_id == sample.accession
            )
            assert (
                ena_sample.get_status_id_display().lower()
                == sample.get_suppression_reason_display().lower()
            )

    @patch("emgena.models.Sample.objects")
    def test_suppress_samples_propagation(self, ena_sample_objs_mock, ena_suppression_propagation_samples):
        ena_sample_objs_mock.using("era").filter.return_value = ena_suppression_propagation_samples

        assert Sample.objects.filter(is_suppressed=True).count() == 0
        assert Run.objects.filter(is_suppressed=True).count() == 0
        assert Assembly.objects.filter(is_suppressed=True).count() == 0
        assert AnalysisJob.objects.filter(is_suppressed=True).count() == 0

        call_command("sync_samples_with_ena")

        assert Sample.objects.filter(is_suppressed=True).count() == 2
        assert Run.objects.filter(is_suppressed=True).count() == 4
        assert Assembly.objects.filter(is_suppressed=True).count() == 8
        assert AnalysisJob.objects.filter(is_suppressed=True).count() == 16
