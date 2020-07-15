#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2020 EMBL - European Bioinformatics Institute
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

from emgapi.models import (Study, AnalysisJob,
                           DownloadGroupType, AnalysisJobDownload)
from emgapianns.models import AnalysisJobTaxonomy

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Remove the results download files and annotations for a study analyses."

    groups = {
        "ITS": [
            "Taxonomic analysis ITS",
            "Taxonomic analysis ITSoneDB",
            "Taxonomic analysis UNITE"
        ],
        "rRNA": [
            "Taxonomic analysis SSU rRNA",
            "Taxonomic analysis LSU rRNA"
        ]
    }

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument("accession", action='store',
                            type=str, help="Study accession")
        parser.add_argument("download_group", help="Download group", type=str,
                            choices=[g for g in self.groups.keys()])
        parser.add_argument(
            '--pipeline',
            help='Pipeline version',
            action='store',
            dest='pipeline',
            choices=[
                '1.0',
                '2.0',
                '3.0',
                '4.0',
                '4.1',
                '5.0'],
            default='5.0'
        )

    def handle(self, *args, **options):

        pipeline_version = options.get("pipeline")
        study_id = int(options.get("accession").replace("MGYS", ""))
        study = Study.objects.get(pk=study_id)

        download_group = options.get("download_group")
        selected_groups = self.groups[download_group]
        groups = DownloadGroupType.objects.filter(group_type__in=selected_groups)

        # Get all the Analysis
        jobs = AnalysisJob.objects.filter(study=study, pipeline__release_version=pipeline_version)

        for job in jobs:
            logger.info("Cleaning job {}".format(job))
            downloads = AnalysisJobDownload.objects.filter(job=job, group_type__in=groups)

            if downloads:
                logger.info("Found {} downloads for job: {}".format(len(downloads), job))
                logger.info("Removing the following files:")
                [logger.info(d.realname) for d in downloads]
                [d.delete() for d in downloads]
                logger.info("Removed.")
            else:
                logger.info("No files to remove.")

            taxonomy_annotations = AnalysisJobTaxonomy.objects.\
                filter(job_id=job.job_id, pipeline_version=pipeline_version)

            if taxonomy_annotations:
                for tax_ann in taxonomy_annotations:
                    if download_group == "ITS":
                        its_onedb = tax_ann.taxonomy_itsonedb
                        if its_onedb and len(its_onedb):
                            logger.info("Removing {} ITS ONE annotations from {}".format(len(its_onedb), job))
                            tax_ann.taxonomy_itsonedb = []

                        its_unite = tax_ann.taxonomy_itsunite
                        if len(its_unite):
                            logger.info("Removing {} ITS Unite annotations from {}".format(len(its_unite), job))
                            tax_ann.taxonomy_itsunite = []

                    if download_group == "rRNA":
                        ssu = tax_ann.taxonomy_ssu
                        if ssu and len(ssu):
                            logger.info("Removing {} SSU annotations from {}".format(len(ssu), job))
                            tax_ann.taxonomy_ssu = []

                        lsu = tax_ann.taxonomy_lsu
                        if lsu and len(lsu):
                            logger.info("Removing {} LSU annotations from {}".format(len(lsu), job))
                            tax_ann.taxonomy_lsu = []

                        tax_ann.save()
            else:
                logger.info("No annotations to remove.")
            logger.info("Job {} is squeaky clean now".format(job))
            logger.info("##########")
