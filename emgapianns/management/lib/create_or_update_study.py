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

from django.db.models import Q
from django.utils import timezone
from ena_portal_api import ena_handler

from emgapi import models as emg_models
from emgapianns.management.commands.import_publication import lookup_publication_by_pubmed_id, \
    update_or_create_publication
from emgapianns.management.lib import utils
from emgena import models as ena_models
from emgena.models import RunStudy, AssemblyStudy

ena = ena_handler.EnaApiHandler()


class StudyImporter(object):
    """
        Creates a new study object in EMG or updates an existing one.
    """

    def __init__(self, secondary_study_accession, study_dir, lineage, ena_db, emg_db):
        self.secondary_study_accession = secondary_study_accession
        self.study_dir = study_dir
        self.lineage = lineage
        self.ena_db = ena_db
        self.emg_db = emg_db

    def run(self):
        logging.info("Creating or updating study {}".format(self.secondary_study_accession))
        ena_study = self._fetch_study_metadata(self.secondary_study_accession, self.ena_db)
        self._update_or_create_study(ena_study, self.study_dir, self.lineage, self.ena_db, self.emg_db)
        logging.info("Finished study {} creation/updating.".format(self.secondary_study_accession))

    @staticmethod
    def _fetch_study_metadata(study_accession, database):
        """
            Fetches latest study metadata from ENA's production database
        :return:
        """
        try:
            study = ena_models.RunStudy.objects.using(database).get(
                Q(study_id=study_accession) | Q(project_id=study_accession))
        except RunStudy.DoesNotExist:
            try:
                study = ena_models.AssemblyStudy.objects.using(database).get(
                    Q(study_id=study_accession) | Q(project_id=study_accession))
            except AssemblyStudy.DoesNotExist:
                raise AssemblyStudy.DoesNotExist(
                    "Could not find study {0} in the ENA database (ERAPRO). Program will exit now!".format(
                        study_accession))
        return study

    @staticmethod
    def _lookup_publication_by_pubmed_ids(pubmed_ids_str):
        emg_publlications = []
        if pubmed_ids_str:
            pubmed_ids = [int(y) for y in list(filter(lambda x: len(x) > 0, pubmed_ids_str.split(',')))]
            for pubmed_id in pubmed_ids:
                europepmc_publications = lookup_publication_by_pubmed_id(pubmed_id)
                for europepmc_publication in europepmc_publications:
                    pub, _ = update_or_create_publication(europepmc_publication)
                    emg_publlications.append(pub)
        return emg_publlications

    def _lookup_publication_by_project_id(self, project_id):
        # TODO: Implement
        pass

    def _update_or_create_study(self, ena_study, study_result_dir, lineage, ena_db, emg_db):
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
        :param ena_study: ENA study - collection of runs.
        :return:
        """

        secondary_study_accession = ena_study.study_id
        data_origination = 'SUBMITTED' if secondary_study_accession.startswith('ERP') else 'HARVESTED'

        hold_date = ena_study.hold_date
        is_public = True if not hold_date else False

        # Retrieve biome object
        biome = emg_models.Biome.objects.using(emg_db).get(lineage=lineage)

        # Lookup study publication
        pubmed_ids = ena_study.pubmed_id
        emg_publications = self._lookup_publication_by_pubmed_ids(pubmed_ids)

        # self._lookup_publication_by_project_id(ena_study.project_id)

        project_id = ena_study.project_id
        if secondary_study_accession.startswith('SRP'):
            project = self._get_ena_project(ena_db, project_id)
            center_name = project.center_name
        else:
            center_name = ena_study.center_name

        defaults = {'centre_name': center_name,
                    'is_public': is_public,
                    'public_release_date': hold_date,
                    'study_abstract': utils.sanitise_string(ena_study.study_description),
                    'study_name': utils.sanitise_string(ena_study.study_title),
                    'study_status': 'FINISHED',
                    'data_origination': data_origination,
                    # README: We want to draw attention to updated studies,
                    # therefore set the date for last updated to today
                    'last_update': timezone.now(),
                    'submission_account_id': ena_study.submission_account_id,
                    'biome': biome,
                    'result_directory': study_result_dir,
                    'first_created': ena_study.first_created}

        study, created = emg_models.Study.objects.using(emg_db).update_or_create(
            project_id=project_id,
            secondary_accession=secondary_study_accession,
            defaults=defaults,
        )

        for pub in emg_publications:
            emg_models.StudyPublication.objects.using(emg_db).update_or_create(
                study=study,
                pub=pub
            )

        return study

    @staticmethod
    def _get_ena_project(ena_db, project_id):
        return ena_models.Project.objects.using(ena_db).get(project_id=project_id)
