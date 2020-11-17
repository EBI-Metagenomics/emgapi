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

from emgapi.models import Study, AnalysisJob, DownloadGroupType, AnalysisJobDownload
from emgapianns.models import AnalysisJobTaxonomy

logger = logging.getLogger(__name__)


def _slugify(string):
    """Converts text to a slug with _ instead of spaces"""
    return string.lower().replace(" ", "_")


class Command(BaseCommand):
    help = (
        "Remove the results download files and/or taxonomic annotations for a study analyses. "
        "Mongo annotations are re-feshed with the exception of the taxonomic ones "
        "(hence the option on this command)"
    )

    def add_arguments(self, parser):
        # we need to get all the Download Groups
        dgroup_slugs = [_slugify(g.group_type) for g in DownloadGroupType.objects.all()]
        dgroup_slugs.append("all")

        super(Command, self).add_arguments(parser)
        parser.add_argument("-a", "--accession", required=True, help="Study accession")
        parser.add_argument(
            "-m",
            "--mongo_tax",
            help="Delete mongo taxonomic annotations",
            action="store_true",
        )
        parser.add_argument(
            "-g",
            "--group",
            nargs="+",
            required=True,
            help="DB Files ONLY, download groups options: %(choices)s",
            metavar="GROUP",
            type=str,
            choices=dgroup_slugs,
        )
        parser.add_argument(
            "--pipeline",
            help="Pipeline version",
            action="store",
            dest="pipeline",
            choices=["1.0", "2.0", "3.0", "4.0", "4.1", "5.0"],
            default="5.0",
        )

    def handle(self, *args, **options):
        """Execute the command"""
        pipeline_version = options.get("pipeline")
        study_id = int(options.get("accession").replace("MGYS", ""))

        try:
            study = Study.objects.get(pk=study_id)
        except Study.DoesNotExist:
            logger.error("Study " + str(study_id) + " doesn't exist")
            return

        download_groups = options.get("group")

        selected_groups = []
        if "all" in download_groups:
            groups = list(DownloadGroupType.objects.all())
        else:
            groups = list(
                g
                for g in DownloadGroupType.objects.all()
                if _slugify(g.group_type) in download_groups
            )

        # Get all the Analysis
        jobs = AnalysisJob.objects.filter(
            study=study, pipeline__release_version=pipeline_version
        )

        logger.info("Analyses jobs to remove: " + str(jobs.count()))

        for job in jobs:
            logger.info("Cleaning analysis job {}".format(job))

            downloads = AnalysisJobDownload.objects.filter(
                job=job,
                group_type__in=groups,
                pipeline__release_version=pipeline_version,
            )

            if downloads:
                logger.info(
                    "Found {} downloads for analysis job: {}".format(
                        len(downloads), job
                    )
                )
                logger.info("Removing the following files:")
                [logger.info(d.realname) for d in downloads]
                downloads.delete()
                logger.info("Removed.")
            else:
                logger.info("No files to remove.")

            if not options.get("mongo_tax"):
                continue

            logger.info("Getting mongo taxonomic annotations.")

            taxonomy_annotations = AnalysisJobTaxonomy.objects.filter(
                job_id=job.job_id, pipeline_version=pipeline_version
            )

            if taxonomy_annotations:
                for tax_ann in taxonomy_annotations:

                    its_onedb = tax_ann.taxonomy_itsonedb
                    if its_onedb:
                        logger.info(
                            "Removing {} ITS ONE annotations from {}".format(
                                len(its_onedb), job
                            )
                        )
                        tax_ann.taxonomy_itsonedb = []

                    its_unite = tax_ann.taxonomy_itsunite
                    if its_unite:
                        logger.info(
                            "Removing {} ITS Unite annotations from {}".format(
                                len(its_unite), job
                            )
                        )
                        tax_ann.taxonomy_itsunite = []

                    ssu = tax_ann.taxonomy_ssu
                    if ssu:
                        logger.info(
                            "Removing {} SSU annotations from {}".format(len(ssu), job)
                        )
                        tax_ann.taxonomy_ssu = []

                    lsu = tax_ann.taxonomy_lsu
                    if lsu:
                        logger.info(
                            "Removing {} LSU annotations from {}".format(len(lsu), job)
                        )
                        tax_ann.taxonomy_lsu = []

                    tax_ann.save()
            else:
                logger.info("No annotations to remove.")
            logger.info("Job {} is squeaky clean now".format(job))
            logger.info("##########")
