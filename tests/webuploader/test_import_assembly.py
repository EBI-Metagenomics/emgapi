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

from emgapianns.management.lib.utils import get_run_accession


def bake_models(coverage=None, min_gap_length=None):
    """Build the required models for import_assembly
    :return: an instance of  emgena.Assembly
    """
    ena_assembly = baker.prepare(
        "emgena.Assembly",
        primary_study_accession="DUMMY_PSA",
        coverage=coverage,
        min_gap_length=min_gap_length,
    )

    emg_study = baker.make(
        "emgapi.Study",
        project_id=ena_assembly.primary_study_accession,
        is_private=False,
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
        assert emg_assembly.coverage == None
        assert emg_assembly.min_gap_length == None
        assert emg_assembly.is_private == False
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

        assert emg_assembly.coverage == 97
        assert emg_assembly.min_gap_length == 30
        assert emg_assembly.is_private == False
        assert emg_assembly.wgs_accession == ena_assembly.wgs_accession
        assert emg_assembly.legacy_accession == ena_assembly.gc_id

    def test_run_accession_getter(self):
        assert get_run_accession("ERR1111111") == "ERR1111111"
        assert get_run_accession("ERR1111111;ERR1111112") == "ERR1111111"  # first only
        assert get_run_accession("PREFIX_ERR1111111") == "ERR1111111"  # only accession part
        assert get_run_accession("ERR1111111_SUFFIX") == "ERR1111111"
        assert get_run_accession("NOPE;PREFIX_ERR1111111_SUFFIX;PREFIX_ERR1111112_SUFFIX;ALSONOPE") == "ERR1111111"  # complete edge case