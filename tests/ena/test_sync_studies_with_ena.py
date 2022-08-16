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
from emgapi.models import Study

from test_utils.emg_fixtures import *  # noqa


@pytest.mark.django_db
class TestSyncENAStudies:
    @patch("emgena.models.Study.objects")
    def test_make_studies_private(self, ena_study_objs_mock, ena_private_studies):
        ena_study_objs_mock.filter.return_value = ena_private_studies

        all_studies = Study.objects.order_by("?").all()
        public_studies = all_studies[0:5]
        reminder = all_studies[5 : len(all_studies)]

        for study in public_studies:
            study.is_private = False

        Study.objects.bulk_update(public_studies, ["is_private"])

        call_command("sync_studies_with_ena")

        all_studies = all_studies.all()  # refresh

        for study in all_studies:
            if study in public_studies:
                assert study.is_private == True

    @patch("emgena.models.Study.objects")
    def test_make_studies_public(self, ena_study_objs_mock, ena_public_studies):
        ena_study_objs_mock.filter.return_value = ena_public_studies

        all_studies = Study.objects.order_by("?").all()
        private_studies = all_studies[0:5]
        reminder = all_studies[5 : len(all_studies)]

        for study in private_studies:
            study.is_private = True

        Study.objects.bulk_update(private_studies, ["is_private"])

        call_command("sync_studies_with_ena")

        all_studies = all_studies.all()  # refresh

        for study in all_studies:
            if study in private_studies:
                assert study.is_private == False

    @patch("emgena.models.Study.objects")
    def test_suppress_studies(self, ena_study_objs_mock, ena_suppressed_studies):
        ena_study_objs_mock.filter.return_value = ena_suppressed_studies

        suppress_studies = Study.objects.order_by("?").all()[0:5]

        for study in suppress_studies:
            study.is_suppressed = False
            study.suppression_reason = None
            study.unsuppress(save=True)

        call_command("sync_studies_with_ena")

        for study in suppress_studies:
            study.refresh_from_db()
            assert study.is_suppressed == True
            ena_study = next(
                e
                for e in ena_suppressed_studies
                if e.study_id == study.secondary_accession
            )
            assert ena_study.hold_date == study.public_release_date
            assert (
                ena_study.get_study_status_display().lower()
                == study.get_suppression_reason_display().lower()
            )
