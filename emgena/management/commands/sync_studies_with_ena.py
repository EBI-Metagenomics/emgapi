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
    help = "Sync the Studies status with ENA"

    def handle(self, *args, **kwargs):
        logging.info("Starting...")

        offset = 0
        batch_size = 1000
        studies_count = emg_models.Study.objects.count()

        logging.info(f"Total studies on EMG {studies_count}")

        while offset < studies_count:
            emg_studies_batch = list(
                emg_models.Study.objects.all()[offset : offset + batch_size]
            )
            ena_studies_batch = ena_models.Study.objects.using("era").filter(
                study_id__in=[study.secondary_accession for study in emg_studies_batch]
            )
            for emg_study in emg_studies_batch:
                ena_study = next(
                    (
                        el
                        for el in ena_studies_batch
                        if el.study_id == emg_study.secondary_accession
                    ),
                    None,
                )
                if ena_study is None:
                    logging.error(f"{emg_study} not found in ENA.")
                    continue
                if ena_study.study_status is None:
                    logging.error(f"{emg_study} on ENA has no value on the column status.")
                    continue

                emg_study.sync_with_ena_status(ena_study.study_status)
                emg_study.public_release_date = ena_study.hold_date

            emg_models.Study.objects.bulk_update(
                emg_studies_batch,
                [
                    "is_private",
                    "is_suppressed",
                    "suppression_reason",
                    "suppressed_at",
                    "public_release_date",
                ],
            )
            logging.info(f"Batch {round(offset / batch_size)} of {round(studies_count / batch_size)} processed.")
            offset += batch_size

        logging.info("Completed")
