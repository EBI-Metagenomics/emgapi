#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2017-2024 EMBL - European Bioinformatics Institute
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
from datetime import timedelta

from django.conf import settings
from django.core.management import BaseCommand
from django.core.paginator import Paginator
from django.utils import timezone

from emgapi.metagenomics_exchange import MetagenomicsExchangeAPI
from emgapi.models import AnalysisJob

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

    def handle(self, *args, **options):
        self.study_accession = options.get("study")
        self.dry_run = options.get("dry_run")
        self.pipeline_version = options.get("pipeline")

        self.mgx_api = MetagenomicsExchangeAPI(
            base_url=settings.METAGENOMICS_EXCHANGE_API
        )

        # never indexed or updated after indexed
        analyses_to_index_and_update = AnalysisJob.objects_for_mgx_indexing.to_add()
        # suppressed only
        analyses_to_delete = AnalysisJob.objects_for_mgx_indexing.to_delete()

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

        for page in Paginator(
            analyses_to_index_and_update,
            settings.METAGENOMICS_EXCHANGE_PAGINATOR_NUMBER,
        ):
            jobs_to_update = []
            for annotation_job in page:
                sequence_accession = ""
                if annotation_job.run:
                    sequence_accession = annotation_job.run.accession
                if annotation_job.assembly:
                    sequence_accession = annotation_job.assembly.accession

                metadata = self.mgx_api.generate_metadata(
                    mgya=annotation_job.accession, sequence_accession=sequence_accession
                )
                registry_id, metadata_match = self.mgx_api.check_analysis(
                    mgya=annotation_job.accession,
                    sequence_accession=sequence_accession,
                    metadata=metadata,
                )
                # The job is not registered
                if not registry_id:
                    logging.info(f"Add new {annotation_job}")
                    if self.dry_run:
                        logging.info(
                            f"Dry-mode run: no addition to real ME for {annotation_job}"
                        )
                        continue

                    response = self.mgx_api.add_analysis(
                        mgya=annotation_job.accession,
                        sequence_accession=sequence_accession,
                    )
                    if response.ok:
                        logging.info(f"Successfully added {annotation_job}")
                        registry_id, metadata_match = self.mgx_api.check_analysis(
                            mgya=annotation_job.accession,
                            sequence_id=sequence_accession,
                        )
                        annotation_job.mgx_accession = registry_id
                        annotation_job.last_mgx_indexed = timezone.now() + timedelta(
                            minutes=1
                        )
                        jobs_to_update.append(annotation_job)
                    else:
                        logging.error(
                            f"Error adding {annotation_job}: {response.message}"
                        )

                # else we have to check if the metadata matches, if not we need to update it
                else:
                    if not metadata_match:
                        logging.info(f"Patch existing {annotation_job}")
                        if self.dry_run:
                            logging.info(
                                f"Dry-mode run: no patch to real ME for {annotation_job}"
                            )
                            continue
                        if self.mgx_api.patch_analysis(
                            registry_id=registry_id, data=metadata
                        ):
                            logging.info(
                                f"Analysis {annotation_job} updated successfully"
                            )
                            # Just to be safe, update the MGX accession
                            annotation_job.mgx_accession = registry_id
                            annotation_job.last_mgx_indexed = (
                                timezone.now() + timedelta(minutes=1)
                            )
                            jobs_to_update.append(annotation_job)
                        else:
                            logging.error(f"Analysis {annotation_job} update failed")
                    else:
                        logging.debug(
                            f"No edit for {annotation_job}, metadata is correct"
                        )

            AnalysisJob.objects.bulk_update(
                jobs_to_update,
                ["last_mgx_indexed", "mgx_accession"],
                batch_size=settings.METAGENOMICS_EXCHANGE_PAGINATOR_NUMBER,
            )

    def process_to_delete_records(self, analyses_to_delete):
        """
        This function removes suppressed records from ME.
        """
        logging.info(f"Processing {len(analyses_to_delete)} analyses to remove")

        for page in Paginator(
            analyses_to_delete, settings.METAGENOMICS_EXCHANGE_PAGINATOR_NUMBER
        ):
            jobs_to_update = []

            for annotation_job in page:
                sequence_accession = ""
                if annotation_job.run:
                    sequence_accession = annotation_job.run.accession
                if annotation_job.assembly:
                    sequence_accession = annotation_job.assembly.accession

                metadata = self.mgx_api.generate_metadata(
                    mgya=annotation_job.accession, sequence_accession=sequence_accession
                )
                registry_id, _ = self.mgx_api.check_analysis(
                    mgya=annotation_job.accession,
                    sequence_accession=sequence_accession,
                    metadata=metadata,
                )
                if registry_id:
                    logging.info(f"Deleting {annotation_job}")
                    if self.dry_run:
                        logging.info(
                            f"Dry-mode run: no delete from real ME for {annotation_job}"
                        )
                        continue

                    if self.mgx_api.delete_analysis(registry_id):
                        logging.info(f"{annotation_job} successfully deleted")
                        annotation_job.last_mgx_indexed = timezone.now()
                        jobs_to_update.append(annotation_job)
                    else:
                        logging.info(f"{annotation_job} failed on delete")
                else:
                    logging.info(
                        f"{annotation_job} doesn't exist in the registry, nothing to delete"
                    )

            # BULK UPDATE #
            AnalysisJob.objects.bulk_update(
                jobs_to_update,
                ["last_mgx_indexed"],
                batch_size=settings.METAGENOMICS_EXCHANGE_PAGINATOR_NUMBER,
            )
