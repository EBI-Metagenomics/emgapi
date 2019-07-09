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
from ena_portal_api import ena_handler
from emgapianns.management.lib.uploader_exceptions import StudyNotBeRetrievedFromENA
from django.apps import apps

ena = ena_handler.EnaApiHandler()


def pull_latest_study_metadata_from_ena_api(study_accession):
    """
        Pulls study information from ENA's API.

    :param study_accession:
    :return:
    """
    try:
        return ena.get_study(primary_accession=study_accession)
    except ValueError:
        try:
            return ena.get_study(secondary_accession=study_accession)
        except ValueError:
            raise StudyNotBeRetrievedFromENA


def pull_latest_study_metadata_from_ena_db(secondary_study_accession, database='era_pro'):
    """
         Pulls study information from database (erapro).

    :param database: Database to query.
    :param secondary_study_accession:
    :return:
    """
    RunStudy = apps.get_model("emgena", "RunStudy")
    return RunStudy.objects.using(database).get(study_id=secondary_study_accession)


def instantiate_study_object(study_raw_metadata_api, study_raw_metadata_db):
    """
        Attributes to parse out:
            - Center name (done)
            - is public (done)
            - release date (done)
            - study abstract (done)
            - primary accession (done)
            - secondary accession (done)
            - study name/title (done)
            - last updated (done)
            - first created (from DB)
            - webin account (from DB)

        Additional not parsable attributes
            - Study status (FINISHED or IN_PROGRESS)
            - data origination (SUBMITTED: EBI or HARVESTED: NCBI)
            - biome_id
            - result directory

        Case:
            1. public read_study, e.g. ERP014351
            2. private read_study, e.g. ERP115605
            3. DRP# study (Asian sequencing archive - DDBJ Sequence Read Archive (DRA)), e.g. DRP003373
            4. ERP# study (European sequencing archive - EBI), e.g. ERP014351
            5. SRP# study (American sequencing archive - NCBI), e.g. SRP042265
            6. study with publication associated, e.g. ERP010597
            7. public analysis_study, e.g. ERP112567
            8. private analysis_study, e.g.

    :param study_raw_metadata:
    :return:
    """
    apps.get_app_config('emgapi')
    Study = apps.get_model("emgapi", "Study")

    first_public = study_raw_metadata_api['first_public'] if 'first_public' in study_raw_metadata_api else None
    is_public = True if 'first_public' in study_raw_metadata_api else False
    new_study = Study.objects.create(
        project_id=study_raw_metadata_api['study_accession'],
        secondary_accession=study_raw_metadata_api['secondary_study_accession'],
        study_abstract=study_raw_metadata_api['description'],
        study_name=study_raw_metadata_api['study_title'],
        # TODO: Confirm with Josie that ENA's API retrieves the correct center name now for SRA accessions
        centre_name=study_raw_metadata_api['center_name'],
        last_update=study_raw_metadata_api['last_updated'],
        public_release_date=first_public,
        first_created=study_raw_metadata_db.first_created,
        submission_account_id=study_raw_metadata_db.submission_account_id,
    )
    # TODO: Process publications
    pubmed_ids = study_raw_metadata_db.pubmed_id


def run_create_or_update_study(study_accession, result_dir_relative_path):
    """
        Both primary and secondary study accessions are support.

        Steps;
            - Check if study already exists
            - Pull latest study metadata from ENA
            - Save or update entry in EMG
    :param study_accession:
    :param result_dir_relative_path: Study result folder, e.g. 2015/08/ERP010251
    :return:
    """
    logging.info("Starting process of creating or updating study in EMG...")
    study_raw_metadata_api = pull_latest_study_metadata_from_ena_api(study_accession)

    secondary_study_accession = study_raw_metadata_api['secondary_study_accession']

    study_raw_metadata_db = pull_latest_study_metadata_from_ena_db(secondary_study_accession)

    instantiate_study_object(study_raw_metadata_api, study_raw_metadata_db)
