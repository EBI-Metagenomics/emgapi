#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2017-2022 EMBL - European Bioinformatics Institute
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

import logging

from django.core.management import BaseCommand

from emgapi.models import AnalysisJob, MetagenomicsExchange, ME_Broker
from emgapi.metagenomics_exchange import MetagenomicsExchangeAPI

logger = logging.getLogger(__name__)

RETRY_COUNT = 5

class Command(BaseCommand):
    help = "Check and populate metagenomics exchange."
    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "-s",
            "--study",
            action="store",
            required=False,
            type=str,
            help="Study accession (rather than all)",
        )
        parser.add_argument(
            "-p",
            "--pipeline",
            help="Pipeline version (rather than all). Not applicable to Genomes.",
            action="store",
            dest="pipeline",
            choices=[1.0, 2.0, 3.0, 4.0, 4.1, 5.0],
            required=False,
            type=float,
        )
        parser.add_argument(
            "-z",
            "--assembly",
            action="store",
            required=False,
            type=str,
            help="Assembly accession (rather than all)",
            nargs="+"
        )
        parser.add_argument(
            "-r",
            "--run",
            action="store",
            required=False,
            type=str,
            help="Run accession (rather than all)",
            nargs="+"
        )
        parser.add_argument(
            "--dev",
            action="store_true",
            required=False,
            help="Populate dev API",
        )
        parser.add_argument(
            "-b",
            "--broker",
            action="store",
            required=False,
            type=str,
            default='EMG',
            help="Broker name",
            choices=["EMG", "MAR"],
        )

    def _filtering_analyses(self):
        analyses = AnalysisJob.objects.all()
        if self.study_accession:
            analyses = analyses.filter(study__secondary_accession=self.study_accession)
        if self.run_accession:
            analyses = analyses.filter(run__accession=self.run_accession)
        if self.assembly_accession:
            analyses = analyses.filter(assembly__accession=self.assembly_accession)
        if self.pipeline_version:
            analyses = analyses.filter(pipeline__pipeline_id=self.pipeline_version)
        return analyses

    def handle(self, *args, **options):
        self.study_accession = options.get("study")
        self.pipeline_version = options.get("pipeline")
        self.assembly_accession = options.get("assembly")
        self.run_accession = options.get("run")

        broker = options.get("broker")
        broker_obj = ME_Broker.objects.get_or_create(broker)
        ME = MetagenomicsExchangeAPI(broker=broker)
        analyses = self._filtering_analyses()

        for analysis in analyses:
            MGYA = analysis.accession
            public = not analysis.is_private
            # check is MGYA in ME
            if ME.check_analysis(source_id=MGYA, public=public):
                logging.info(f"{MGYA} exists in ME")
            else:
                logging.info(f"{MGYA} does not exist in ME")
                response = ME.add_record(mgya=MGYA, run_accession=analysis.run, public=public)
                if response.status_code == 201:
                    logging.info(f"Populating MetagenomicsExchange table with {MGYA}")
                    MetagenomicsExchange.objects.get_or_create(analysis, broker=broker_obj)
                else:
                    logging.error(f"{MGYA} response exit code: {response.status_code}. No population to DB.")


