#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2021 EMBL - European Bioinformatics Institute
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

from unittest.mock import patch

import pytest

from emgapi import models as emg_models

from emgapianns.management.commands.import_assembly import Command

from model_bakery import baker


def bake_models(coverage=None, min_gap_length=None):
    """Build the required models for import_assembly
    :return: an instance of  emgena.Assembly
    """
    # Status models are created on a migration
    status, _ = emg_models.Status.objects.get_or_create(status="public", status_id=4)

    ena_assembly = baker.prepare(
        "emgena.Assembly",
        primary_study_accession="DUMMY_PSA",
        coverage=coverage,
        min_gap_length=min_gap_length,
        status_id=status.status_id,
    )

    emg_study = baker.make(
        "emgapi.Study",
        project_id=ena_assembly.primary_study_accession,
        is_public=True,
    )
    emg_sample = baker.make("emgapi.Sample", accession=ena_assembly.sample_id)
    emg_experyment_type = baker.make(
        "emgapi.ExperimentType", experiment_type="assembly"
    )
    return ena_assembly


class TestImportAssembly:
    @patch("emgapianns.management.commands.import_assembly.Command.get_ena_db_assembly")
    @pytest.mark.django_db(transaction=True)
    def test_import_assembly(self, mock_get_assembly):
        """Test import assembly, without coverage or min_gap_length"""

        ena_assembly = bake_models()

        mock_get_assembly.return_value = ena_assembly

        BIOME = "root:Environmental:Terrestrial:Fake"
        cmd = Command()
        cmd.run_from_argv(
            argv=[
                "manage.py",
                "import_assembly",
                ena_assembly.assembly_id,
                "--biome",
                BIOME,
            ]
        )

        emg_assembly = emg_models.Assembly.objects.get(
            accession=ena_assembly.assembly_id
        )

        status = emg_models.Status.objects.get(status="public")

        assert emg_assembly.coverage == None
        assert emg_assembly.min_gap_length == None
        assert emg_assembly.status_id == status
        assert emg_assembly.wgs_accession == ena_assembly.wgs_accession
        assert emg_assembly.legacy_accession == ena_assembly.gc_id

    @patch("emgapianns.management.commands.import_assembly.Command.get_ena_db_assembly")
    @pytest.mark.django_db(transaction=True)
    def test_import_assembly_with_cov(self, mock_get_assembly):
        """Test import assembly, with coverage and min_gap_length"""

        ena_assembly = bake_models(coverage=97, min_gap_length=30)

        mock_get_assembly.return_value = ena_assembly

        BIOME = "root:Environmental:Terrestrial:Soil"
        cmd = Command()
        cmd.run_from_argv(
            argv=[
                "manage.py",
                "import_assembly",
                ena_assembly.assembly_id,
                "--biome",
                BIOME,
            ]
        )

        emg_assembly = emg_models.Assembly.objects.get(
            accession=ena_assembly.assembly_id
        )

        status = emg_models.Status.objects.get(status="public")

        assert emg_assembly.coverage == 97
        assert emg_assembly.min_gap_length == 30
        assert emg_assembly.status_id == status
        assert emg_assembly.wgs_accession == ena_assembly.wgs_accession
        assert emg_assembly.legacy_accession == ena_assembly.gc_id
