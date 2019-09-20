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
import sys

from django.db.models import Q
from ena_portal_api import ena_handler

from emgapianns.management.lib import utils
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


def lookup_publication_by_pubmed_ids(pubmed_ids):
    # TODO: Implement
    pass


def lookup_publication_by_project_id(project_id):
    # TODO: Implement
    pass


def update_or_create_study(study, study_result_dir, lineage, database):
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

    :param biome_id: biome identifier.
    :param study_result_dir: e.g. 2018/08/SRP042265
    :param study: ENA study - collection of runs.
    :return:
    """

    secondary_study_accession = study.study_id
    data_origination = 'SUBMITTED' if secondary_study_accession.startswith('ERP') else 'HARVESTED'

    hold_date = study.hold_date
    # first_public = hold_date if hold_date else None # TODO
    is_public = True if not hold_date else False

    # Retrieve biome object
    biome = emg_models.Biome.objects.get(lineage=lineage)

    # Lookup study publication
    # TODO: Process publications
    pubmed_ids = study.pubmed_id
    # pubmed_id_list = pubmed_ids.split(',') # TODO
    lookup_publication_by_pubmed_ids(pubmed_ids)

    lookup_publication_by_project_id(study.project_id)

    project_id = study.project_id
    if secondary_study_accession.startswith('SRP'):
        project = ena_models.Project.objects.using(database).get(project_id=project_id)
        center_name = project.center_name
    else:
        center_name = study.center_name

    # new_study = Study.objects.using(database).update_or_create(
    return emg_models.Study.objects.update_or_create(
        project_id=project_id,
        secondary_accession=secondary_study_accession,
        defaults={'centre_name': center_name,
                  'is_public': is_public,
                  'public_release_date': hold_date,
                  'study_abstract': utils.sanitise_string(study.study_description),
                  'study_name': utils.sanitise_string(study.study_title),
                  'study_status': 'FINISHED',
                  'data_origination': data_origination,
                  'last_update': study.last_updated,
                  'submission_account_id': study.submission_account_id,
                  'biome': biome,
                  'result_directory': study_result_dir,
                  'first_created': study.first_created},
    )


def run_create_or_update_study(study_accession, study_dir, lineage, database):
    """
        Creates a new study object in EMG or updates an existing one.

    :param study_accession:
    :param study_dir: Root path to EMG's archive
    :param lineage: biome identifier
    :param database: Pointer to the database connection details in the config file.
    :return:
    """
    logging.info("Starting process of creating or updating study in EMG...")

    # Fetches latest study metadata from ENA's production database
    study = ena_models.RunStudy.objects.using(database).get(Q(study_id=study_accession) | Q(project_id=study_accession))
    if not study:
        study = ena_models.AssemblyStudy.objects.using(database).get(
            Q(study_id=study_accession) | Q(project_id=study_accession))
        if not study:
            raise ValueError("Could not find study {0} in the database. Program will exit now!".format(study_accession))

    return update_or_create_study(study, study_dir, lineage, database)
