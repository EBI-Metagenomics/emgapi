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

from unittest.mock import patch

import pytest
from django.utils import timezone

from emgapi import models as emg_models
from emgapianns.management.commands.import_study import Command
from emgena import models as ena_models


def mock_ena_run_study(*args, **kwargs):
    study = ena_models.RunStudy()
    study.study_id = 'ERP117125'
    study.project_id = 'PRJEB34249'
    study.study_status = 'public'
    study.center_name = 'UNIVERSITY OF CAMBRIDGE'
    study.hold_date = None
    study.first_created = '2019-09-04 11:23:26'
    study.last_updated = '2019-09-04 11:23:26'
    study.study_title = 'Dysbiosis associated with acute helminth infections in herbivorous youngstock - '
    'observations and implications'
    study.study_description = 'This study investigates, for the first time, the associations between acute '
    'infections by GI helminths and the faecal microbial and metabolic profiles of '
    'a cohort of equine youngstock, prior to and following treatment with '
    'parasiticides (ivermectin).'
    study.submission_account_id = 'Webin-50804'
    study.pubmed_id = ''
    return study, []


def mock_ncbi_run_study_SRP000125():
    """
        Useful tests for this case:
            List of pubmed_ids
    :return:
    """
    study = ena_models.RunStudy()
    study.study_id = 'SRP000125'
    study.project_id = 'PRJNA17765'
    study.study_status = 'public'
    study.center_name = 'SDSU Center for Universal Microbial Sequencing'
    study.hold_date = None
    study.first_created = '2010-02-26'
    study.last_updated = '2017-09-25'
    study.study_title = 'Marine phages from the Gulf of Mexico'
    study.study_description = 'A combined set of 41 samples was isolated by the Suttle Laboratory from 13 ' \
                              'different sites in the Gulf of Mexico between June 1, 1994 and July 31, 2001.  ' \
                              'The phage fraction was purified and sequenced using pyrophosphate sequencing ' \
                              '(454 Life Sciences).    This is part of a global ocean survey of phage and ' \
                              'virus sequences.   454 sequence data is available from the Short Read Archive ' \
                              '(SRA): <a href="ftp://ftp.ncbi.nih.gov/pub/TraceDB/ShortRead/SRA000408  ' \
                              '">SRA000408</a>.   Metagenomics SEED ID: 4440304.3  Nature paper ID: 32  ' \
                              'The WGS project can be found using the Project data link.'
    study.submission_account_id = 'Webin-842'
    study.pubmed_id = '17090214,18337718'
    return study, []


def get_ena_project_mock(center_name):
    project = ena_models.Project()
    project.center_name = center_name
    project.project_id = 'PRJEB34249'
    return project


def mock_ncbi_run_study_SRP034734():
    """
        Useful tests for this case:
            pubmed_id = None
            Center name for BioProjects

    :return:
    """
    study = ena_models.RunStudy()
    study.study_id = 'SRP034734'
    study.project_id = 'PRJNA218849'
    study.study_status = 'public'
    study.center_name = 'Veer Narmad South Gujarat University'
    study.hold_date = None
    study.first_created = '2014-01-09'
    study.last_updated = '2017-07-10'
    study.study_title = 'Lonar Lake sediment Metagenome'
    study.study_description = 'Understanding the relevance of bacterial and archaeal diversity in the ' \
                              'soda lake sediments by the culture independent approach using bTEFAP.  ' \
                              'Lonar Lake is a saline soda lake located at Lonar in Buldana district, ' \
                              'Maharashtra State, India, which was created by a meteor impact.'
    study.submission_account_id = 'Webin-842'
    study.pubmed_id = None
    return study, []


def insert_biome(biome_id, biome_name, left, right, depth, lineage):
    emg_models.Biome.objects.update_or_create(biome_id=biome_id,
                                              biome_name=biome_name,
                                              defaults={'lft': left,
                                                        'rgt': right,
                                                        'depth': depth,
                                                        'lineage': lineage})


@pytest.mark.django_db(reset_sequences=True, transaction=True)
class TestImportStudyTransactions:

    @patch('emgapianns.management.commands.import_study.Command.get_study_dir')
    @patch('emgapianns.management.lib.create_or_update_study.StudyImporter._fetch_study_metadata')
    def test_import_ena_study_should_succeed(self, mock_db, mock_study_dir):
        """
        :param mock_db:
        :param mock_study_dir:
        :return:
        """
        accession = 'ERP117125'
        lineage = 'root:Host-associated:Mammals:Digestive system:Fecal'
        biome_name = 'Fecal'

        mock_study_dir.return_value = "2019/09/ERP117125"
        mock_db.return_value = expected = mock_ena_run_study()

        insert_biome(422, biome_name, 841, 844, 5, lineage)

        with mock_db, mock_study_dir:
            cmd = Command()
            cmd.run_from_argv(
                argv=['manage.py', 'import_study', accession, lineage])
            actual_study = emg_models.Study.objects.get(secondary_accession=accession)
            assert expected[0].study_id == actual_study.secondary_accession
            assert expected[0].project_id == actual_study.project_id
            assert expected[0].center_name == actual_study.centre_name
            assert None is actual_study.experimental_factor
            assert True is actual_study.is_public
            assert None is actual_study.public_release_date
            assert expected[0].study_description == actual_study.study_abstract
            assert expected[0].study_title == actual_study.study_name
            assert 'FINISHED' == actual_study.study_status
            assert 'SUBMITTED' == actual_study.data_origination
            assert None is actual_study.author_email
            assert None is actual_study.author_name
            assert timezone.now().strftime("%m/%d/%Y") == actual_study.last_update.strftime("%m/%d/%Y")
            assert expected[0].submission_account_id == actual_study.submission_account_id
            assert biome_name == actual_study.biome.biome_name
            assert mock_study_dir.return_value == actual_study.result_directory
            assert expected[0].first_created == actual_study.first_created.strftime("%Y-%m-%d %H:%M:%S")
            assert 0 == len(actual_study.publications.all())
            assert 0 == len(actual_study.samples.all())

    @patch('emgapianns.management.lib.create_or_update_study.StudyImporter._get_ena_project')
    @patch('emgapianns.management.commands.import_study.Command.get_study_dir')
    @patch('emgapianns.management.lib.create_or_update_study.StudyImporter._fetch_study_metadata')
    def test_import_ncbi_study_SRP000125_should_succeed(self, mock_db, mock_study_dir, mock_ena_project):
        """
        :param mock_db:
        :param mock_study_dir:
        :return:
        """
        accession = 'SRP000125'
        lineage = 'root:Host-associated:Mammals:Digestive system:Fecal'
        biome_name = 'Fecal'

        mock_study_dir.return_value = "2019/09/{}".format(accession)
        mock_db.return_value = expected = mock_ncbi_run_study_SRP000125()
        mock_ena_project.return_value = get_ena_project_mock('SDSU Center for Universal Microbial Sequencing')

        insert_biome(422, biome_name, 841, 844, 5, lineage)

        with mock_db, mock_study_dir, mock_ena_project:
            cmd = Command()
            cmd.run_from_argv(
                argv=['manage.py', 'import_study', accession, lineage])
            actual_study = emg_models.Study.objects.get(secondary_accession=accession)
            assert expected[0].study_id == actual_study.secondary_accession
            assert expected[0].project_id == actual_study.project_id
            assert expected[0].center_name == actual_study.centre_name
            assert None is actual_study.experimental_factor
            assert True is actual_study.is_public
            assert None is actual_study.public_release_date
            assert expected[0].study_description == actual_study.study_abstract
            assert expected[0].study_title == actual_study.study_name
            assert 'FINISHED' == actual_study.study_status
            assert 'HARVESTED' == actual_study.data_origination
            assert None is actual_study.author_email
            assert None is actual_study.author_name
            assert timezone.now().strftime("%m/%d/%Y") == actual_study.last_update.strftime("%m/%d/%Y")
            assert expected[0].submission_account_id == actual_study.submission_account_id
            assert biome_name == actual_study.biome.biome_name
            assert mock_study_dir.return_value == actual_study.result_directory
            assert expected[0].first_created == actual_study.first_created.strftime("%Y-%m-%d")
            assert 2 == len(actual_study.publications.all())
            assert 0 == len(actual_study.samples.all())

    @patch('emgapianns.management.lib.create_or_update_study.StudyImporter._get_ena_project')
    @patch('emgapianns.management.commands.import_study.Command.get_study_dir')
    @patch('emgapianns.management.lib.create_or_update_study.StudyImporter._fetch_study_metadata')
    def test_import_ncbi_study_SRP034734_should_succeed(self, mock_db, mock_study_dir, mock_ena_project):
        """
        :param mock_db:
        :param mock_study_dir:
        :return:
        """
        accession = 'SRP034734'
        lineage = 'root:Host-associated:Mammals:Digestive system:Fecal'
        biome_name = 'Fecal'
        #
        mock_study_dir.return_value = "2019/09/{}".format(accession)
        mock_db.return_value = expected = mock_ncbi_run_study_SRP034734()
        mock_ena_project.return_value = get_ena_project_mock('Veer Narmad South Gujarat University')
        #
        insert_biome(422, biome_name, 841, 844, 5, lineage)

        with mock_db, mock_study_dir, mock_ena_project:
            cmd = Command()
            cmd.run_from_argv(
                argv=['manage.py', 'import_study', accession, lineage])
            actual_study = emg_models.Study.objects.get(secondary_accession=accession)
            assert expected[0].study_id == actual_study.secondary_accession
            assert expected[0].project_id == actual_study.project_id
            assert expected[0].center_name == actual_study.centre_name
            assert None is actual_study.experimental_factor
            assert True is actual_study.is_public
            assert None is actual_study.public_release_date
            assert expected[0].study_description == actual_study.study_abstract
            assert expected[0].study_title == actual_study.study_name
            assert 'FINISHED' == actual_study.study_status
            assert 'HARVESTED' == actual_study.data_origination
            assert None is actual_study.author_email
            assert None is actual_study.author_name
            assert timezone.now().strftime("%m/%d/%Y") == actual_study.last_update.strftime("%m/%d/%Y")
            assert expected[0].submission_account_id == actual_study.submission_account_id
            assert biome_name == actual_study.biome.biome_name
            assert mock_study_dir.return_value == actual_study.result_directory
            assert expected[0].first_created == actual_study.first_created.strftime("%Y-%m-%d")
            assert 0 == len(actual_study.publications.all())
            assert 0 == len(actual_study.samples.all())
