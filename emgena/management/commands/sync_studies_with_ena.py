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
import os

from django.db.models import Count
from django.core.management import BaseCommand
from django.conf import settings

from emgapi import models as emg_models
from emgena import models as ena_models

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync the Studies status with ENA"

    def handle(self, *args, **kwargs):
        logger.info("Starting...")

        offset = 0
        batch_size = 1000
        studies_count = emg_models.Study.objects.count()

        logger.info(f"Total {model_name} on EMG {emg_model_count}")

        while offset < studies_count:
            emg_studies_batch = emg_model.objects.all[offset, batch_size]
            ena_studies_batch = ena_models.Study.objects.filter(
                study_id__in=[study.secondary_accession for study in emg_studies_batch]
            )
            for emg_study in emg_studies_batch:
                ena_study = next(
                    (el for el in ena_studies_batch if el.study_id == study.secondary_accession),
                    default=None,
                )
                if ena_study is None:
                    logger.error(f"{study} not found in ENA.")
                    continue
                if ena_study.status is None:
                    logger.error(f"{study} on ENA has no value on the column status.")
                    continue
                emg_study.sync_with_ena_status(ena_study.status)
                emg_study.public_release_date = ena_study.hold_date

            emg_models.Study.objects.bulk_update(
                emg_studies_batch, ["is_private", "is_suppressed", "reason", "public_release_date"]
            )
            logger.info(f"Batch {studies_count / batch_size::.0f} processed.")
            offset += batch_size

        logger.info("Completed")
