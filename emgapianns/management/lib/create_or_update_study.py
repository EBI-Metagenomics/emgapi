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
from emgapi import models as emg_models
from emgena import models as ena_models

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


def pull_latest_study_metadata_from_ena_db(secondary_study_accession, database):
    """
         Pulls study information from database (erapro).

    :param database: Database to query.
    :param secondary_study_accession:
    :return:
    """
    return ena_models.RunStudy.objects.using(database).get(study_id=secondary_study_accession)


def lookup_publication_by_pubmed_ids(pubmed_ids):
    # TODO: Implement
    pass


def lookup_publication_by_project_id(project_id):
    # TODO: Implement
    pass


def instantiate_study_object(run_study, result_directory, biome_id):
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
            - data origination (SUBMITTED: EBI or HARVESTED: NCBI or DDJB)
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

    :param run_study:
    :return:
    """

    secondary_study_accession = run_study.study_id
    data_origination = 'SUBMITTED' if secondary_study_accession.startswith('ERP') else 'HARVESTED'

    hold_date = run_study.hold_date
    first_public = hold_date if hold_date else None
    is_public = True if not hold_date else False

    # Retrieve biome object
    biome = emg_models.Biome.objects.get(pk=biome_id)

    # Lookup study publication
    # TODO: Process publications
    pubmed_ids = run_study.pubmed_id
    pubmed_id_list = pubmed_ids.split(',')
    lookup_publication_by_pubmed_ids(pubmed_ids)

    lookup_publication_by_project_id(run_study.project_id)

    # new_study = Study.objects.using(database).update_or_create(
    new_study = emg_models.Study.objects.update_or_create(
        project_id=run_study.project_id,
        secondary_accession=secondary_study_accession,
        defaults={'centre_name': run_study.center_name,
                  'is_public': is_public,
                  'public_release_date': hold_date,
                  'study_abstract': run_study.study_description,
                  'study_name': run_study.study_title,
                  'study_status': 'FINISHED',
                  'data_origination': data_origination,
                  'last_update': run_study.last_updated,
                  'submission_account_id': run_study.submission_account_id,
                  'biome': biome,
                  'result_directory': result_directory,
                  'first_created': run_study.first_created},
    )


def run_create_or_update_run_study(secondary_study_accession, result_dir_relative_path, biome_id, database='era_pro'):
    """
        Both primary and secondary study accessions are support.

        Steps;
            - Check if study already exists
            - Pull latest study metadata from ENA
            - Save or update entry in EMG
    :param database: Pointer to the database connection details in the config file.
    :param secondary_study_accession: e.g. ERP014351 or SRP042265
    :param result_dir_relative_path: Study result folder, e.g. 2015/08/ERP010251
    :return:
    """
    logging.info("Starting process of creating or updating study in EMG...")

    run_study = pull_latest_study_metadata_from_ena_db(secondary_study_accession, database)

    instantiate_study_object(run_study, result_dir_relative_path, biome_id)


def run_create_or_update_assembly_study(secondary_study_accession, result_dir_relative_path, database='era_pro'):
    # TODO: Implement
    pass
