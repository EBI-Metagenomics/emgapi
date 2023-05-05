#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 EMBL - European Bioinformatics Institute
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

from django.core.management import BaseCommand, call_command

from emgapianns.management.lib import utils
from emgapianns.management.lib.utils import sanitise_fields, is_run_accession
from ena_portal_api import ena_handler
from emgapi import models as emg_models
from emgena import models as ena_models

logger = logging.getLogger(__name__)

ena = ena_handler.EnaApiHandler()


class Command(BaseCommand):
    help = "Imports new objects into EMG."

    obj_list = list()
    rootpath = None
    genome_folders = None

    emg_db = None
    ena_db = None
    biome = None

    def add_arguments(self, parser):
        parser.add_argument("accessions", help="ENA analysis accessions", nargs="+")
        parser.add_argument(
            "--ena_db", help="ENA's production database enapro", default="ena"
        )
        parser.add_argument(
            "--emg_db",
            help="Target emg_db_name alias",
            choices=["default", "dev", "prod"],
            default="default",
        )
        parser.add_argument("--biome", help="Lineage of GOLD biome")

    def handle(self, *args, **options):
        logger.info("CLI %r" % options)
        self.emg_db = options["emg_db"]
        self.ena_db = options["ena_db"]
        self.biome = options["biome"]

        for acc in options["accessions"]:
            logger.info("Importing assembly {}".format(acc))
            self.import_assembly(acc)
            logger.info("Assembly import finished successfully.")

    def import_assembly(self, accession):
        db_assembly_data = self.get_ena_db_assembly(accession)
        assembly = self.create_or_update_assembly(db_assembly_data)
        sample = self.tag_sample(assembly, db_assembly_data.sample_id)
        self.tag_study(assembly, db_assembly_data.primary_study_accession, sample)

        assembly.is_private = assembly.study.is_private
        assembly.save()

        self.tag_experiment_type(assembly, "assembly")
        self.tag_optional_run(assembly, db_assembly_data.name)

        assembly.save(using=self.emg_db)

    def get_ena_db_assembly(self, accession):
        logger.info("Fetching assembly {} from ena oracle DB".format(accession))
        return ena_models.Assembly.objects.using(self.ena_db).get(assembly_id=accession)

    def create_or_update_assembly(self, ena_assembly):
        accession = ena_assembly.assembly_id
        logger.info("Creating assembly {}".format(accession))
        defaults = sanitise_fields({
            "is_private": ena_assembly.status_id == 2,
            "is_suppressed": ena_assembly.status_id in [3, 5 ,6],
            "wgs_accession": ena_assembly.wgs_accession,
            "legacy_accession": ena_assembly.gc_id,
            "coverage": ena_assembly.coverage,
            "min_gap_length": ena_assembly.min_gap_length
        })
        assembly, created = emg_models.Assembly.objects.using(self.emg_db).update_or_create(
            accession=accession,
            defaults=defaults
        )
        return assembly

    def tag_study(self, assembly, study_accession, sample):
        try:
            _study = emg_models.Study.objects.using(self.emg_db) \
                .get(project_id=study_accession)
            assembly.study = _study
            emg_models.StudySample.objects.using(self.emg_db).get_or_create(study=_study, sample=sample)
        except emg_models.Study.DoesNotExist:
            raise emg_models.Study.DoesNotExist("Study {} does not exist in emg DB".format(study_accession))

    def tag_sample(self, assembly, sample_accession):
        try:
            sample = emg_models.Sample.objects.using(self.emg_db) \
                .get(accession=sample_accession)
            emg_models.AssemblySample.objects.using(self.emg_db).get_or_create(assembly=assembly, sample=sample)
            return sample
        except emg_models.Sample.DoesNotExist:
            raise emg_models.Sample.DoesNotExist("Sample {} does not exist in emg DB".format(sample_accession))

    def tag_experiment_type(self, assembly, experiment_type):
        try:
            assembly.experiment_type = emg_models.ExperimentType.objects.using(self.emg_db) \
                .get(experiment_type=experiment_type.lower())
        except emg_models.ExperimentType.DoesNotExist:
            raise emg_models.ExperimentType \
                .DoesNotExist("Experiment type {} does not exist in database".format(experiment_type))

    def tag_optional_run(self, assembly, name):
        logging.info(f"Retrieving runs for the assembly name {name}")
        run_accession = utils.get_run_accession(name)
        if run_accession and is_run_accession(run_accession):
            self.tag_run(assembly, run_accession)
        else:
            logging.warning("Could not retrieve run accession from assembly name!")

        logging.info(
            "Checking if there are additional runs in ENA, required for hybrid assemblies"
        )
        try:
            ena_run_accessions = (
                ena.get_assembly(
                    assembly_name=assembly.accession,
                    fields="run_accession",
                    data_portal="ena",
                )
                .get("run_accession", [])
                .split(";")
            )
            for ena_run_accession in ena_run_accessions:
                if not ena_run_accession == run_accession:
                    logging.info(
                        "Assembly has additional run: {}".format(ena_run_accession)
                    )
                    self.tag_run(assembly, ena_run_accession)
        except ValueError as e:
            logging.exception(e)
            logging.info(f"Could not retrive the runs for the assembly {assembly}")

    def tag_run(self, assembly, run_accession):
        try:
            call_command("import_run", run_accession, "--biome", self.biome)
            run = emg_models.Run.objects.using(self.emg_db) \
                .get(accession=run_accession)
            emg_models.AssemblyRun.objects.using(self.emg_db).get_or_create(assembly=assembly, run=run)
        except emg_models.Run.DoesNotExist:
            raise emg_models.Run \
                .DoesNotExist("Run {} does not exist in database".format(run_accession))
