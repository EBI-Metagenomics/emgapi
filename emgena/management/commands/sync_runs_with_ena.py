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

from emgapi import models as emg_models
from emgena import models as ena_models


class Command(BaseCommand):
    help = "Sync the Runs status with ENA"

    def handle(self, *args, **kwargs):
        logging.info("Starting...")

        offset = 0
        batch_size = 1000
        runs_count = emg_models.Run.objects.count()

        logging.info(f"Total Runs on EMG {runs_count}")

        while offset < runs_count:
            emg_runs_batch = emg_models.Run.objects.all()[offset: offset + batch_size]
            ena_runs_batch = ena_models.Run.objects.using("era").filter(
                run_id__in=[run.accession for run in emg_runs_batch]
            )

            for emg_run in emg_runs_batch:
                ena_run = next(
                    (el for el in ena_runs_batch if el.run_id == emg_run.accession),
                    None,
                )
                if ena_run is None:
                    logging.error(f"{emg_run} not found in ENA.")
                    continue
                if ena_run.status_id is None:
                    logging.error(f"{emg_run} on ENA has no value on the column status.")
                    continue
                emg_run.sync_with_ena_status(ena_run.status_id)

            emg_models.Run.objects.bulk_update(
                emg_runs_batch,
                ["is_private", "is_suppressed", "suppression_reason", "suppressed_at"],
            )
            logging.info(f"Batch {round(offset / batch_size)} of {round(runs_count / batch_size)} processed.")
            offset += batch_size

        logging.info("Completed")
