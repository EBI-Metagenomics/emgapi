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
import csv
import os

from django.core.management import BaseCommand
from django.conf import settings
from django.core.paginator import Paginator

from emgapi.models import Study, AnalysisJob, Pipeline, AnalysisJobDownload

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Check for missing download files for all (or any) study."

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "-o",
            "--output",
            action="store",
            required=False,
            default="download_files_report.tsv",
            type=str,
        )
        parser.add_argument(
            "-s",
            "--study",
            action="store",
            required=False,
            type=str,
            help="Study accession",
        )
        parser.add_argument(
            "-p",
            "--pipeline",
            help="Pipeline version",
            action="store",
            dest="pipeline",
            choices=["1.0", "2.0", "3.0", "4.0", "4.1", "5.0"],
            required=False,
        )

    def handle(self, *args, **options):
        """Review all the download files for all the studies."""

        study_accession = options.get("study")
        pipeline_version = options.get("pipeline")
        out_tsv = options.get("output")

        download_files = AnalysisJobDownload.objects.all()

        if study_accession:
            study = Study.objects.get(accession=study_accession)
            download_files = download_files.filter(study=study)

        if pipeline_version:
            pipeline = Pipeline.objects.get(release_version=pipeline_version)
            download_files = download_files.filter(job__pipeline=pipeline)

        with open(out_tsv, "w", newline="") as tsvfile:
            tsv_writer = csv.writer(tsvfile, delimiter="\t")
            tsv_writer.writerow(
                [
                    "file_id",
                    "file_path",
                    "job_accession",
                    "study_accession",
                    "unzipped?",
                ]
            )

            paginator = Paginator(download_files, 50)

            for page_index in range(1, paginator.num_pages + 1):

                page = paginator.page(page_index)
                logger.debug(
                    "Processing page: "
                    + str(page_index)
                    + " of "
                    + str(paginator.num_pages)
                )

                for d_file in page.object_list:

                    d_file_path = "/{0}/{1}".format(
                        d_file.job.study.result_directory, d_file.realname
                    )

                    if d_file.subdir is not None:
                        d_file_path = "/{0}/{1}/{2}".format(
                            d_file.job.study.result_directory,
                            d_file.subdir,
                            d_file.realname,
                        )

                    file_path = os.path.join(settings.RESULTS_DIR, d_file_path)

                    if not os.path.exists(file_path):
                        logging.debug("Missing file: " + file_path)
                        unzipped_exists = None
                        # if gzipped try with no extension
                        if file_path.endswith(".gz"):
                            unzipped_exists = os.path.exists(file_path[:3])
                            if unzipped_exists:
                                logging.debug(
                                    "--- but uncompressed file exists: " + file_path[:3]
                                )
                        tsv_writer.writerow(
                            [
                                d_file.pk,
                                file_path,
                                d_file.job.study.accession,
                                d_file.job.accession,
                                unzipped_exists,
                            ]
                        )
