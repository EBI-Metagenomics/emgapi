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
from django.core.management import call_command
from django.core.exceptions import ValidationError
from model_bakery import baker
from test_utils.emg_fixtures import *  # noqa

from emgapi import models as emg_models
from emgena import models as ena_models
from emgapianns.management.commands.import_assembly import Command


FAKE_ENA_RESPONSE = {
    "sample_accession": "SAMN03418252",
    "study_accession": "PRJNA278393",
    "secondary_study_accession": "SRP056480",
    "run_accession": "FAKE_RUN_ACCESSION",
    "library_source": "METAGENOMIC",
    "library_strategy": "WGS",
    "library_layout": "PAIRED",
    "fastq_ftp": "ftp.sra.ebi.ac.uk/vol1/fastq/SRR192/009/SRR1927149/SRR1927149_1.fastq.gz;ftp.sra.ebi.ac.uk/vol1/fastq/SRR192/009/SRR1927149/SRR1927149_2.fastq.gz",
    "fastq_md5": "8c56e0fa7605eec74d609dd4679f25a3;3cda0c29b86ffea0c870227788dc1a1d",
    "fastq_bytes": "1400715326;1368210512",
    "base_count": 2830033596,
    "read_count": 14834811,
    "instrument_platform": "ILLUMINA",
    "instrument_model": "Illumina Genome Analyzer IIx",
    "secondary_sample_accession": "SRS882224",
    "library_name": "",
    "sample_alias": "10001",
    "sample_title": "This sample has been submitted by pda|rampelli85 on 2015-05-27; human gut metagenome",
    "sample_description": "Human Gut Microbiome of Hadza subject 1",
    "first_public": "2015-06-05",
    "status": "public", # Public
}


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("experiment_type")
class TestImportAssembly:
    @patch("emgapianns.management.commands.import_run.Command.get_run_api")
    def test_import_run(self, mock_get_run, biome):
        """Test import run - with no study"""

        sample = baker.make(
            "emgapi.Sample", accession="SRS882224", biome=biome, is_private=False
        )

        mock_get_run.return_value = FAKE_ENA_RESPONSE

        call_command(
            "import_run", "FAKE_RUN_ACCESSION", "--biome", biome.lineage,
        )

        run = emg_models.Run.objects.get(accession="FAKE_RUN_ACCESSION")

        assert run.study is None
        assert run.accession == mock_get_run.return_value["run_accession"]
        assert (
            run.ena_study_accession
            == mock_get_run.return_value["secondary_study_accession"]
        )
        assert run.is_private == False
        assert run.sample == sample
        assert (
            run.instrument_platform == mock_get_run.return_value["instrument_platform"]
        )
        assert run.instrument_model == mock_get_run.return_value["instrument_model"]

    @patch("emgapianns.management.commands.import_run.Command.get_run_api")
    def test_import_run_invalid_study_accession(self, mock_get_run, biome):
        """Test import run - with an invalid study accession"""

        baker.make("emgapi.Sample", accession="SRS882224", biome=biome, is_private=False)

        ena_response = FAKE_ENA_RESPONSE
        ena_response[
            "secondary_study_accession"
        ] = "TRP056480"  # Invalid Study accession
        mock_get_run.return_value = ena_response

        with pytest.raises(ValidationError):
            call_command("import_run", "FAKE_RUN_ACCESSION", "--biome", "root:foo:bar")

    @patch(
        "emgapianns.management.lib.create_or_update_study.StudyImporter._get_ena_project"
    )
    @patch("emgapianns.management.commands.import_study.Command.get_study_dir")
    @patch(
        "emgapianns.management.lib.create_or_update_study.StudyImporter._fetch_study_metadata"
    )
    @patch("emgapianns.management.commands.import_run.Command.get_run_api")
    def test_import_run_with_import_study(
        self,
        mock_get_run,
        mock_study_metada,
        mock_study_dir,
        mock_ena_project,
        biome,
        ena_run_study,
    ):
        """Test import run - and import the study too.
        This is an integration test as it will pull the Study data from ENA
        """
        sample = baker.make(
            "emgapi.Sample", accession="SRS882224", biome=biome, is_private=False
        )

        ena_response = FAKE_ENA_RESPONSE
        ena_response["secondary_study_accession"] = ena_run_study.study_id
        mock_get_run.return_value = ena_response

        mock_study_metada.return_value = [ena_run_study, []]
        mock_study_dir.return_value = "2019/09/ERP117125"
        mock_ena_project.return_value = ena_models.Project(project_id="PRJNA278393")

        call_command(
            "import_run",
            "FAKE_RUN_ACCESSION",
            "--biome",
            "root:foo:bar",
            "--import-study",
        )

        run = emg_models.Run.objects.get(accession="FAKE_RUN_ACCESSION")

        assert run.study == emg_models.Study.objects.get(
            secondary_accession=mock_get_run.return_value["secondary_study_accession"]
        )
        assert run.accession == mock_get_run.return_value["run_accession"]
        assert run.ena_study_accession is None
        assert run.is_private == False
        assert run.sample == sample
        assert (
            run.instrument_platform == mock_get_run.return_value["instrument_platform"]
        )
        assert run.instrument_model == mock_get_run.return_value["instrument_model"]
