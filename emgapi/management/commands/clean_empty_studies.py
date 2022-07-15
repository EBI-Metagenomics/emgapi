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

from emgapi.models import Study, StudySample, AnalysisJob, Run, Status, Sample

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Check for missing download files for all (or any) study."

    def handle(self, *args, **kwargs):
        logger.info("Starting to cleanup the 'empty studies'")

        studies = Study.objects.exclude(is_public=Status.SUPRESSED)
        for study in studies:
            # only those with no jobs
            if AnalysisJob.objects.filter(study=study).exists():
                continue
            # the study must be linked to other studies
            # through the samples
            samples = StudySample.objects.filter(study=study).values_list(
                "sample_id", flat=True
            )
            sample_study_counts = StudySample.objects.filter(
                sample_id__in=samples
            ).aggregate(Count("study", distinct=True))
            if sample_study_counts["study__count"] < 2:
                # This is likely an empty study due to a partial update
                logger.info(f"{study} with no linked to other studies")
                continue

            logger.info(f"Updating the {study} runs...")
            runs = Run.objects.filter(study=study)
            for run in runs:
                run.ena_study_accession = study.secondary_accession
                run.study = None
            Run.objects.bulk_update(runs, ["ena_study_accession", "study"])
            study.is_public = Status.SUPRESSED
            study.save()
            logger.info(f"{study} suppressed")
