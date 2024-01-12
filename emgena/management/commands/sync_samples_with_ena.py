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
    help = "Sync the Samples status with ENA"

    def handle(self, *args, **kwargs):
        logging.info("Starting...")

        offset = 0
        batch_size = 1000
        samples_count = emg_models.Sample.objects.count()

        logging.info(f"Total Samples on EMG {samples_count}")

        while offset < samples_count:
            # TODO: review this rule, I didn't have enough time to review it.
            # ported from: https://github.com/EBI-Metagenomics/mi-automation/blob/develop/legacy_production/tools/production/emg-object-status-checker.py#L242
            emg_samples_batch = list(
                emg_models.Sample.objects.exclude(accession__startswith="GCA_")[
                    offset : offset + batch_size
                ]
            )
            ena_samples_batch = ena_models.Sample.objects.using("era").filter(
                sample_id__in=[sample.accession for sample in emg_samples_batch]
            )

            for emg_sample in emg_samples_batch:
                ena_sample = next(
                    (
                        el
                        for el in ena_samples_batch
                        if el.sample_id == emg_sample.accession
                    ),
                    None,
                )
                if ena_sample is None:
                    logging.error(f"{emg_sample} not found in ENA.")
                    continue
                if ena_sample.status_id is None:
                    logging.error(
                        f"{emg_sample} on ENA has no value on the column status."
                    )
                    continue
                emg_sample.sync_with_ena_status(ena_sample.status_id)

            emg_models.Sample.objects.bulk_update(
                emg_samples_batch,
                ["is_private", "is_suppressed", "suppression_reason", "suppressed_at"],
            )
            logging.info(f"Batch {round(samples_count / batch_size)} processed.")
            offset += batch_size

        logging.info("Completed")
