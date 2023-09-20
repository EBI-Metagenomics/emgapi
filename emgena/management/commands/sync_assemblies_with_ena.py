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


class Command(BaseCommand):
    help = "Sync the Assemblies status with ENA"

    def handle(self, *args, **kwargs):
        logging.info("Starting...")

        offset = 0
        batch_size = 1000
        assemblies_count = emg_models.Assembly.objects.exclude(
            study__isnull=True
        ).count()

        logging.info(f"Total Assemblies on EMG {assemblies_count}")

        while offset < assemblies_count:
            emg_assemblies_batch = list(
                emg_models.Assembly.objects.all()
                .exclude(study__isnull=True)
                .select_related("study")[offset : offset + batch_size]
            )
            ena_assemblies_batch = ena_models.Assembly.objects.using("ena").filter(
                gc_id__in=[
                    assembly.legacy_accession for assembly in emg_assemblies_batch
                ]
            )
            for emg_assembly in emg_assemblies_batch:
                ena_assembly = next(
                    (
                        el
                        for el in ena_assemblies_batch
                        if el.gc_id == emg_assembly.legacy_accession
                    ),
                    None,
                )
                study = emg_assembly.study

                if ena_assembly is None:
                    logging.debug(
                        f"{emg_assembly} not found in ENA. The assembly inherits from the study: {study}"
                    )
                    if not study:
                        logging.error(
                            f"{emg_assembly} not found in ENA, and the assembly doesn't have a study."
                        )
                        continue

                    # inherits the privacy status of its study
                    emg_assembly.is_private = study.is_private
                    continue
                elif ena_assembly.status_id is None:
                    logging.error(
                        f"{emg_assembly} on ENA has no value on the column status."
                    )
                    continue

                # It's possible that the assembly and the study have different public/private values
                # if they are different, the study takes precedence
                if ena_assembly.status_id == ena_models.Status.PRIVATE and (
                    study and not study.is_private
                ):
                    logging.info(
                        f"Mismatch between the study and the assembly. Using the study, {emg_assembly}.is_private={study.is_private} now."
                    )
                    emg_assembly.is_private = study.is_private
                else:
                    emg_assembly.sync_with_ena_status(ena_assembly.status_id)

            emg_models.Assembly.objects.bulk_update(
                emg_assemblies_batch,
                ["is_private", "is_suppressed", "suppression_reason", "suppressed_at"],
            )
            logging.info(f"Batch {round(assemblies_count / batch_size)} processed.")
            offset += batch_size

        logging.info("Completed")
