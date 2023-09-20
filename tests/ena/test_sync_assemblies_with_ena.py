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
from emgapi.models import Assembly, AnalysisJob

from test_utils.emg_fixtures import *  # noqa


@pytest.mark.django_db
class TestSyncENAAssemblies:
    @patch("emgena.models.Assembly.objects")
    def test_make_assemblies_private(
        self, ena_assemblies_objs_mock, ena_private_assemblies
    ):
        ena_assemblies_objs_mock.using(
            "ena"
        ).filter.return_value = ena_private_assemblies

        public_assemblies = Assembly.objects.order_by("?").all()[0:5]

        for assembly in public_assemblies:
            assembly.is_private = False

        Assembly.objects.bulk_update(public_assemblies, ["is_private"])

        call_command("sync_assemblies_with_ena")

        for assembly in public_assemblies:
            assembly.refresh_from_db()
            assert assembly.is_private == True

    @patch("emgena.models.Assembly.objects")
    def test_make_assemblies_public(
        self, ena_assembly_objs_mock, ena_public_assemblies
    ):
        ena_assembly_objs_mock.using("ena").filter.return_value = ena_public_assemblies

        private_assemblies = Assembly.objects.order_by("?").all()[0:5]

        for assembly in private_assemblies:
            assembly.is_private = True

        Assembly.objects.bulk_update(private_assemblies, ["is_private"])

        call_command("sync_assemblies_with_ena")

        for assembly in private_assemblies:
            assembly.refresh_from_db()
            assert assembly.is_private == False

    @patch("emgena.models.Assembly.objects")
    def test_suppress_assemblies(
        self, ena_assembly_objs_mock, ena_suppressed_assemblies
    ):
        ena_assembly_objs_mock.using(
            "ena"
        ).filter.return_value = ena_suppressed_assemblies

        suppressed_assemblies = Assembly.objects.order_by("?").all()[0:5]

        for assembly in suppressed_assemblies:
            assembly.is_suppressed = False
            assembly.suppression_reason = None
            assembly.unsuppress(save=True)

        call_command("sync_assemblies_with_ena")

        for assembly in suppressed_assemblies:
            assembly.refresh_from_db()
            assert assembly.is_suppressed == True
            ena_assembly = next(
                e
                for e in ena_suppressed_assemblies
                if e.gc_id == assembly.legacy_accession
            )
            assert (
                ena_assembly.get_status_id_display().lower()
                == assembly.get_suppression_reason_display().lower()
            )

    @patch("emgena.models.Assembly.objects")
    def test_sync_assemblies_based_on_study(
        self, ena_assembly_objs_mock, ena_private_assemblies
    ):
        ena_assembly_objs_mock.using("ena").filter.return_value = ena_private_assemblies

        assemblies = Assembly.objects.order_by("?").all()[0:5]

        for assembly in assemblies:
            assembly.study.is_private = False
            assembly.study.save()
            assert assembly.is_private == True

        call_command("sync_assemblies_with_ena")

        for assembly in assemblies:
            assembly.refresh_from_db()
            assert assembly.is_suppressed == False
            assert assembly.is_private == False


    @patch("emgena.models.Assembly.objects")
    def test_sync_assemblies_propagation(
        self, ena_assembly_objs_mock, ena_suppression_propagation_assemblies
    ):
        ena_assembly_objs_mock.using("ena").filter.return_value = ena_suppression_propagation_assemblies

        assert Assembly.objects.filter(is_suppressed=True).count() == 0
        assert AnalysisJob.objects.filter(is_suppressed=True).count() == 0

        call_command("sync_assemblies_with_ena")

        assert Assembly.objects.filter(is_suppressed=True).count() == 32
        assert AnalysisJob.objects.filter(
            is_suppressed=True,
            suppression_reason=AnalysisJob.Reason.ANCESTOR_SUPPRESSED
        ).count() == 64
