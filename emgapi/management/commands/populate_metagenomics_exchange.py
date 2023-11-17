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
import responses

from django.conf import settings
from django.core.management import BaseCommand

from emgapi.models import AnalysisJob
from emgapi.metagenomics_exchange import MetagenomicsExchangeAPI

logger = logging.getLogger(__name__)

RETRY_COUNT = 5

class Command(BaseCommand):
    help = "Check and populate metagenomics exchange (ME)."
    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "-s",
            "--study",
            required=False,
            type=str,
            help="Study accession list (rather than all)",
            nargs='+',
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
            "--dev",
            action="store_true",
            required=False,
            help="Populate dev API",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            required=False,
            help="Dry mode, no population of ME",
        )
        # TODO: do I need it?
        parser.add_argument(
            "--full",
            action="store_true",
            help="Do a full check of DB",
        )

    def generate_metadata(self, mgya, run_accession, status):
        return {
            "confidence": "full",
            "endPoint": f"https://www.ebi.ac.uk/metagenomics/analyses/{mgya}",
            "method": ["other_metadata"],
            "sourceID": mgya,
            "sequenceID": run_accession,
            "status": status,
            "brokerID": settings.MGNIFY_BROKER,
        }

    def handle(self, *args, **options):
        self.study_accession = options.get("study")
        self.dry_run = options.get("dry_run")
        self.pipeline_version = options.get("pipeline")
        if options.get("dev"):
            base_url = settings.ME_API_DEV
        else:
            base_url = settings.ME_API
        ME = MetagenomicsExchangeAPI(base_url=base_url)

        new_analyses = AnalysisJob.objects_for_population.to_add()
        removals = AnalysisJob.objects_for_population.to_delete()
        if self.study_accession:
            new_analyses = new_analyses.filter(study__secondary_accession__in=self.study_accession)
            removals = removals.filter(study__secondary_accession__in=self.study_accession)
        if self.pipeline_version:
            new_analyses = new_analyses.filter(pipeline__pipeline_id=self.pipeline_version)
            removals = removals.filter(pipeline__pipeline_id=self.pipeline_version)
        logging.info(f"Processing {len(new_analyses)} new analyses")
        for ajob in new_analyses:
            metadata = self.generate_metadata(mgya=ajob.accession, run_accession=ajob.run,
                                              status="public" if not ajob.is_private else "private")
            registryID, metadata_match = ME.check_analysis(source_id=ajob.accession, metadata=metadata)
            if not registryID:
                logging.debug(f"Add new {ajob}")
                if not self.dry_run:
                    response = ME.add_analysis(mgya=ajob.accession, run_accession=ajob.run, public=not ajob.is_private)
                    if response.ok:
                        logging.debug(f"Added {ajob}")
                    else:
                        logging.debug(f"Error adding {ajob}: {response.message}")
                else:
                    logging.info(f"Dry-mode run: no addition to real ME for {ajob}")
            else:
                if not metadata_match:
                    logging.debug(f"Patch existing {ajob}")
                    if not self.dry_run:
                        if ME.patch_analysis(registry_id=registryID, data=metadata):
                            logging.info(f"Analysis {ajob} updated successfully")
                        else:
                            logging.info(f"Analysis {ajob} update failed")
                    else:
                        logging.info(f"Dry-mode run: no patch to real ME for {ajob}")
                else:
                    logging.debug(f"No edit for {ajob}, metadata is correct")

        logging.info(f"Processing {len(removals)} analyses to remove")
        for ajob in removals:
            metadata = self.generate_metadata(mgya=ajob.accession, run_accession=ajob.run,
                                              status="public" if not ajob.is_private else "private")
            registryID, _ = ME.check_analysis(source_id=ajob.accession, metadata=metadata)
            if registryID:
                if not self.dry_run:
                    if ME.delete_analysis(registryID):
                        logging.info(f"{ajob} successfully deleted")
                    else:
                        logging.info(f"{ajob} failed on delete")
                else:
                    logging.info(f"Dry-mode run: no delete from real ME for {ajob}")
            else:
                logging.info(f"No {ajob} in ME, nothing to delete")
        logging.info("Done")





