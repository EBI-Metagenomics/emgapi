#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2022 EMBL - European Bioinformatics Institute
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

from emgapi.models import Study, Pipeline, AnalysisJobDownload, StudyDownload, AssemblyExtraAnnotation, \
    Assembly, GenomeDownload, Genome, GenomeCatalogue, GenomeCatalogueDownload

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Check for missing download files for studies, analyses, assemblies, genomes and catalogues."

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
            help="Study accession (rather than all)",
        )
        parser.add_argument(
            "-p",
            "--pipeline",
            help="Pipeline version (rather than all). Not applicable to Genomes.",
            action="store",
            dest="pipeline",
            choices=["1.0", "2.0", "3.0", "4.0", "4.1", "5.0"],
            required=False,
        )
        parser.add_argument(
            "-g",
            "--genome",
            action="store",
            required=False,
            type=str,
            help="Genome accession (rather than all)",
        )
        parser.add_argument(
            "-c",
            "--catalogue",
            action="store",
            required=False,
            type=str,
            help="Genome catalogue ID (rather than all)",
        )
        parser.add_argument(
            "-a",
            "--analysis",
            action="store",
            required=False,
            type=str,
            help="Analysis accession (rather than all)",
        )
        parser.add_argument(
            "-z",
            "--assembly",
            action="store",
            required=False,
            type=str,
            help="Assembly accession (rather than all)",
        )

    @staticmethod
    def _check_unzipped(file_path: str):
        unzipped_exists = None
        # if gzipped try with no extension
        if file_path.endswith(".gz"):
            unzipped_exists = os.path.exists(file_path[:3])
            if unzipped_exists:
                logging.debug(
                    "--- but uncompressed file exists: " + file_path[:3]
                )
        return unzipped_exists

    def _handle_studies(self, study_accession: str, tsv_writer: csv.writer):
        download_files = StudyDownload.objects.all()

        if study_accession:
            study = Study.objects.get(accession=study_accession)
            download_files = download_files.filter(study=study)

        paginator = Paginator(download_files, 50)

        for page_index, page in enumerate(paginator):
            logger.info(f"Processing study page {page_index + 1} of {paginator.num_pages}")

            for d_file in page.object_list:

                d_file_path = "{0}/{1}".format(
                    d_file.job.study.result_directory, d_file.realname
                )

                if d_file.subdir is not None:
                    d_file_path = "{0}/{1}/{2}".format(
                        d_file.job.study.result_directory,
                        d_file.subdir,
                        d_file.realname,
                    )

                file_path = os.path.join(settings.RESULTS_DIR, d_file_path)

                if not os.path.exists(file_path):
                    logging.info("Missing file: " + file_path)
                    unzipped_exists = self._check_unzipped(file_path)
                    tsv_writer.writerow(
                        [
                            'Study',
                            f"MGYS{d_file.study.study_id:0>8}",
                            "",
                            d_file.__class__.__name__,
                            d_file.pk,
                            file_path,
                            unzipped_exists,
                        ]
                    )

    def _handle_assemblies(self, assembly_accession: str, tsv_writer: csv.writer):
        download_files = AssemblyExtraAnnotation.objects.all()

        if assembly_accession:
            assembly = Assembly.objects.get(accession=assembly_accession)
            download_files = download_files.filter(assembly=assembly)

        paginator = Paginator(download_files, 50)

        for page_index, page in enumerate(paginator):
            logger.info(f"Processing assembly page {page_index + 1} of {paginator.num_pages}")

            for d_file in page.object_list:
                d_file_path = f"{d_file.subdir}/{d_file.realname}"

                file_path = os.path.join(settings.RESULTS_DIR, d_file_path)

                if not os.path.exists(file_path):
                    logging.info("Missing file: " + file_path)
                    unzipped_exists = self._check_unzipped(file_path)
                    tsv_writer.writerow(
                        [
                            'Assembly',
                            str(d_file.assembly.accession),
                            f"MGYS{d_file.assembly.study.study_id:0>8}",
                            d_file.__class__.__name__,
                            d_file.pk,
                            file_path,
                            unzipped_exists,
                        ]
                    )

    def _handle_genomes(self, genome_accession: str, genome_catalogue_id: str, tsv_writer: csv.writer):
        download_files = GenomeDownload.objects.all()

        if genome_catalogue_id:
            catalogue = GenomeCatalogue.objects.get(catalogue_id=genome_catalogue_id)
            download_files = download_files.filter(genome__catalogue=catalogue)

        if genome_accession:
            genome = Genome.objects.get(accession=genome_accession)
            download_files = download_files.filter(genome=genome)

        paginator = Paginator(download_files, 50)

        for page_index, page in enumerate(paginator):
            logger.info(f"Processing genome page {page_index + 1} of {paginator.num_pages}")

            for d_file in page.object_list:
                d_file_path = f"{d_file.genome.result_directory}/{d_file.realname}"
                if d_file.subdir:
                    d_file_path = f"{d_file.genome.result_directory}/{d_file.subdir}/{d_file.realname}"

                file_path = os.path.join(settings.RESULTS_DIR, d_file_path)

                if not os.path.exists(file_path):
                    logging.info("Missing file: " + file_path)
                    unzipped_exists = self._check_unzipped(file_path)
                    tsv_writer.writerow(
                        [
                            'Genome',
                            d_file.genome.accession,
                            d_file.genome.catalogue_id,
                            d_file.__class__.__name__,
                            d_file.pk,
                            file_path,
                            unzipped_exists,
                        ]
                    )

    def _handle_catalogues(self, genome_catalogue_id: str, tsv_writer: csv.writer):
        download_files = GenomeCatalogueDownload.objects.all()

        if genome_catalogue_id:
            catalogue = GenomeCatalogue.objects.get(catalogue_id=genome_catalogue_id)
            download_files = download_files.filter(genome__catalogue=catalogue)

        paginator = Paginator(download_files, 50)

        for page_index, page in enumerate(paginator):
            logger.info(f"Processing catalogue page {page_index + 1} of {paginator.num_pages}")

            for d_file in page.object_list:
                d_file_path = f"{d_file.genome_catalogue.result_directory}/{d_file.realname}"
                if d_file.subdir:
                    d_file_path = f"{d_file.genome_catalogue.result_directory}/{d_file.subdir}/{d_file.realname}"

                file_path = os.path.join(settings.RESULTS_DIR, d_file_path)

                if not os.path.exists(file_path):
                    logging.info("Missing file: " + file_path)
                    unzipped_exists = self._check_unzipped(file_path)
                    tsv_writer.writerow(
                        [
                            'GenomeCatalogue',
                            d_file.genome_catalogue.catalogue_id,
                            "",
                            d_file.__class__.__name__,
                            d_file.pk,
                            file_path,
                            unzipped_exists,
                        ]
                    )

    def _handle_analyses(
            self,
            analysis_accession: str,
            study_accession: str,
            pipeline_version: str,
            tsv_writer: csv.writer
    ):
        download_files = AnalysisJobDownload.objects.all()

        if analysis_accession:
            download_files.filter(job__id=int(analysis_accession.lstrip('MGYA')))

        if study_accession:
            study = Study.objects.get(accession=study_accession)
            download_files = download_files.filter(study=study)

        if pipeline_version:
            pipeline = Pipeline.objects.get(release_version=pipeline_version)
            download_files = download_files.filter(job__pipeline=pipeline)

        paginator = Paginator(download_files, 50)

        for page_index, page in enumerate(paginator):
            logger.info(
                "Processing page: "
                + str(page_index + 1)
                + " of "
                + str(paginator.num_pages)
            )

            for d_file in page.object_list:

                d_file_path = "{0}/{1}".format(
                    d_file.job.study.result_directory, d_file.realname
                )

                if d_file.subdir is not None:
                    d_file_path = "{0}/{1}/{2}".format(
                        d_file.job.study.result_directory,
                        d_file.subdir,
                        d_file.realname,
                    )

                file_path = os.path.join(settings.RESULTS_DIR, d_file_path)

                if not os.path.exists(file_path):
                    logging.info("Missing file: " + file_path)
                    unzipped_exists = self._check_unzipped(file_path)
                    tsv_writer.writerow(
                        [
                            'Analysis',
                            f"MGYA{d_file.job.job_id:0>8}",
                            f"MGYS{d_file.job.study.study_id:0>8}",
                            d_file.__class__.__name__,
                            d_file.pk,
                            file_path,
                            unzipped_exists,
                        ]
                    )

    def handle(self, *args, **options):
        """Review all the download files"""

        study_accession = options.get("study")
        pipeline_version = options.get("pipeline")
        genome_accession = options.get("genome")
        genome_catalogue_id = options.get("catalogue")
        analysis_accession = options.get("analysis")
        assembly_accession = options.get("assembly")

        out_tsv = options.get("output")

        do_study = bool(study_accession)
        do_genome = bool(genome_accession)
        do_catalogue = bool(genome_catalogue_id)
        do_analysis = bool(analysis_accession) or bool(pipeline_version)
        do_assembly = bool(assembly_accession)

        do_all = not any((do_study, do_genome, do_catalogue, do_analysis, do_assembly))
        with open(out_tsv, "w", newline="") as tsvfile:
            tsv_writer = csv.writer(tsvfile, delimiter="\t")
            tsv_writer.writerow(
                [
                    "object_type",
                    "accession",
                    "related_accession",
                    "download_type",
                    "download_id",
                    "file_path",
                    "unzipped?",
                ]
            )

            if do_all or do_study:
                self._handle_studies(study_accession, tsv_writer)

            if do_all or do_assembly:
                self._handle_assemblies(assembly_accession, tsv_writer)

            if do_all or do_analysis or do_study:
                self._handle_analyses(analysis_accession, study_accession, pipeline_version, tsv_writer)

            if do_all or do_genome or do_catalogue:
                self._handle_genomes(genome_accession, genome_catalogue_id, tsv_writer)

            if do_all or do_catalogue:
                self._handle_catalogues(genome_catalogue_id, tsv_writer)