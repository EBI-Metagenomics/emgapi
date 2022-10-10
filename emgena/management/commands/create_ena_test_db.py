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

from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django.db import connections, OperationalError

import emgena.models as ena_models

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Creates tables and data in fake ENA db, for use with minimal "
    ena_db_label = None

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--ena_db',
                            help="The (test) ENA database connection label to use, from settings",
                            default='era')

    def create_table_for_model(self, model):
        with connections[self.ena_db_label].schema_editor() as schema_editor:
            try:
                schema_editor.create_model(model)
            except OperationalError:
                logger.warning(f'Table {model._meta.db_table} already existed')

    def handle(self, *args, **options):
        self.ena_db_label = options.get('ena_db')
        ena_db = settings.DATABASES.get(self.ena_db_label)
        if not ena_db:
            raise CommandError('No ENA DATABASE')
        if 'sqlite' not in ena_db.get('ENGINE'):
            raise CommandError('Not running this script against a non-SQLite (testing) database!')

        # Webin accounts
        self.create_table_for_model(ena_models.Submitter)
        self.create_table_for_model(ena_models.SubmitterContact)
        webin = ena_models.SubmitterContact.objects.using(self.ena_db_label).create(
            first_name='FirstName',
            surname='SurName',
            submission_account='Webin-000'
        )
        ena_models.Submitter.objects.using(self.ena_db_label).create(
            submission_account=webin,
            analysis=False,
            submitter=True
        )

        # Studies
        self.create_table_for_model(ena_models.RunStudy)
        ena_models.RunStudy.objects.using(self.ena_db_label).create(
            study_id='ERP136943',
            project_id='PRJEB52249',
            study_status='public',
            center_name='EMG',
            hold_date=None,
            first_created='2022-04-09',
            last_updated='2022-04-09',
            study_title='EMG produced TPA metagenomics assembly of PRJNA530339 data set (Shotgun Metagenomics of 361 post-menopause women reveals gut microbiome change along with the bone loss).',
            study_description="The Third Party Annotation (TPA) assembly was derived from the primary whole genome shotgun (WGS) data set PRJNA530339, and was assembled with SPAdes v3.14.1. This project includes samples from the following biomes: root:Host-associated:Human:Digestive system.",
            submission_account_id='Webin-460',
            pubmed_id='29069476',
        )

        # Projects
        self.create_table_for_model(ena_models.Project)
        ena_models.Project.objects.using(self.ena_db_label).create(
            project_id='PRJEB52249',
            center_name='EMG'
        )

        # Samples
        self.create_table_for_model(ena_models.Sample)
        ena_models.Sample.objects.using(self.ena_db_label).create(
            sample_id='SRS4579074',
            submission_id='SRA869361',
            biosample_id='SAMN11311563',
            submission_account_id='Webin-842',
            first_created='2020-01-03',
            last_updated='2021-03-02',
            first_public='2020-01-03',
            status_id=4,
            tax_id='408170',
            scientific_name='human gut metagenome',
            title='CL100042219_L01_29',
            alias='CL100042219_L01_29',
            checklist=None
        )

        # GCS Assembly
        self.create_table_for_model(ena_models.AssemblyMapping)
        ena_models.AssemblyMapping.objects.using(self.ena_db_label).create(
            accession="ERZ8153470",
            submission_account="Webin-460",
            name='SRR8845517_57e20239ca1e2c722893b3590fd45cd7',
            legacy_accession='GCA_937633295',
            legacy_version='1',
            wgs_accession=None,
            sample_id='SRS4579074',
            biosample_id='SAMN11311563',
            submission_id='ERA12210947',
            status=2,
            assembly_type='primary metagenome',
            project_accession='PRJEB52249',
            coverage=55,
            contig_accession_range='ERZ8153470.1-ERZ8153470.29114'
        )