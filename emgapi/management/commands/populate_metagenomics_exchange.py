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

from django.conf import settings
from django.core.management import BaseCommand
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta

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
            nargs="+",
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
            "--dry-run",
            action="store_true",
            required=False,
            help="Dry mode, no population of ME",
        )

    def generate_metadata(self, mgya, run_accession, status):
        return {
            "confidence": "full",
            "endPoint": f"https://www.ebi.ac.uk/metagenomics/analyses/{mgya}",
            "method": ["other_metadata"],
            "sourceID": mgya,
            "sequenceID": run_accession,
            "status": status,
            "brokerID": settings.METAGENOMICS_EXCHANGE_MGNIFY_BROKER,
        }

    def handle(self, *args, **options):
        self.study_accession = options.get("study")
        self.dry_run = options.get("dry_run")
        self.pipeline_version = options.get("pipeline")

        self.mgx_api = MetagenomicsExchangeAPI(base_url=settings.METAGENOMICS_EXCHANGE_API)

        # never indexed or updated after indexed
        analyses_to_index_and_update = AnalysisJob.objects_for_mgx_indexing.to_add()
        # suppressed only
        analyses_to_delete = AnalysisJob.objects_for_mgx_indexing.get_suppressed()

        if self.study_accession:
            analyses_to_index_and_update = analyses_to_index_and_update.filter(
                study__secondary_accession__in=self.study_accession
            )
            analyses_to_delete = analyses_to_delete.filter(
                study__secondary_accession__in=self.study_accession
            )

        if self.pipeline_version:
            analyses_to_index_and_update = analyses_to_index_and_update.filter(
                pipeline__release_version=self.pipeline_version
            )
            analyses_to_delete = analyses_to_delete.filter(
                pipeline__release_version=self.pipeline_version
            )

        self.process_to_index_and_update_records(analyses_to_index_and_update)
        self.process_to_delete_records(analyses_to_delete)

        logging.info("Done")


    def process_to_index_and_update_records(self, analyses_to_index_and_update):
        logging.info(f"Indexing {len(analyses_to_index_and_update)} new analyses")

        for page in Paginator(analyses_to_index_and_update, 100):
            jobs_to_update = []

            for ajob in page:
                metadata = self.generate_metadata(
                    mgya=ajob.accession,
                    run_accession=ajob.run,
                    status="public" if not ajob.is_private else "private",
                )
                registry_id, metadata_match = self.mgx_api.check_analysis(
                    source_id=ajob.accession, sequence_id=ajob.run, metadata=metadata
                )
                # The job is not registered
                if not registry_id:
                    logging.info(f"Add new {ajob}")
                    if self.dry_run:
                        logging.info(f"Dry-mode run: no addition to real ME for {ajob}")
                        continue

                    response = self.mgx_api.add_analysis(
                        mgya=ajob.accession,
                        run_accession=ajob.run,
                        public=not ajob.is_private,
                    )
                    if response.ok:
                        logging.info(f"Successfully added {ajob}")
                        registry_id, metadata_match = self.mgx_api.check_analysis(
                            source_id=ajob.accession, sequence_id=ajob.run)
                        ajob.mgx_accession = registry_id
                        ajob.last_mgx_indexed = timezone.now() + timedelta(minutes=1)
                        jobs_to_update.append(ajob)
                    else:
                        logging.error(f"Error adding {ajob}: {response.message}")

                # else we have to check if the metadata matches, if not we need to update it
                else:
                    if not metadata_match:
                        logging.info(f"Patch existing {ajob}")
                        if self.dry_run:
                            logging.info(
                                f"Dry-mode run: no patch to real ME for {ajob}"
                            )
                            continue
                        if self.mgx_api.patch_analysis(
                                registry_id=registry_id, data=metadata
                        ):
                            logging.info(f"Analysis {ajob} updated successfully")
                            # Just to be safe, update the MGX accession
                            ajob.mgx_accession = registry_id
                            ajob.last_mgx_indexed = timezone.now()
                            jobs_to_update.append(ajob)
                        else:
                            logging.error(f"Analysis {ajob} update failed")
                    else:
                        logging.debug(f"No edit for {ajob}, metadata is correct")

            AnalysisJob.objects.bulk_update(
                jobs_to_update, ["last_mgx_indexed", "mgx_accession"], batch_size=100
            )

    def process_to_delete_records(self, analyses_to_delete):
        """
        This function removes suppressed records from ME.
        """
        logging.info(f"Processing {len(analyses_to_delete)} analyses to remove")

        for page in Paginator(analyses_to_delete, 100):
            jobs_to_update = []

            for ajob in page:
                metadata = self.generate_metadata(
                    mgya=ajob.accession,
                    run_accession=ajob.run,
                    status="public" if not ajob.is_private else "private",
                )
                registry_id, _ = self.mgx_api.check_analysis(
                    source_id=ajob.accession, sequence_id=ajob.run, metadata=metadata
                )
                if registry_id:
                    logging.info(f"Deleting {ajob}")
                    if self.dry_run:
                        logging.info(f"Dry-mode run: no delete from real ME for {ajob}")
                        continue

                    if self.mgx_api.delete_analysis(registry_id):
                        logging.info(f"{ajob} successfully deleted")
                        ajob.last_mgx_indexed = timezone.now()
                        jobs_to_update.append(ajob)
                    else:
                        logging.info(f"{ajob} failed on delete")
                else:
                    logging.info(
                        f"{ajob} doesn't exist in the registry, nothing to delete"
                    )

            # BULK UPDATE #
            AnalysisJob.objects.bulk_update(
                jobs_to_update, ["last_mgx_indexed"], batch_size=100
            )
