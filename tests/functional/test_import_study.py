from unittest.mock import patch

import pytest
from django.test import TransactionTestCase
from django.utils import timezone
from test_utils.emg_fixtures import *  # noqa

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
    return study


def insert_biome(biome_id, biome_name, left, right, depth, lineage):
    emg_models.Biome.objects.update_or_create(biome_id=biome_id,
                                              biome_name=biome_name,
                                              defaults={'lft': left,
                                                        'rgt': right,
                                                        'depth': depth,
                                                        'lineage': lineage})


@pytest.mark.django_db
class TestImportStudyTransactions(TransactionTestCase):

    @pytest.mark.usefixtures("biome")
    @pytest.mark.usefixtures("var_names")
    # @pytest.mark.parametrize("accession, lineage", [
    #     ('ERP117125', 'root:Host-associated:Mammals:Digestive system:Fecal')
    # ])
    @patch('emgapianns.management.commands.import_study.Command.get_study_dir')
    @patch('emgapianns.management.lib.create_or_update_study.StudyImporter._fetch_study_metadata')
    def test_import_study_should_succeed(self, mock_db, mock_study_dir):
        """
        :param mock_db:
        :param mock_study_dir:
        :return:
        """
        accession = 'ERP117125'
        lineage = 'root:Host-associated:Mammals:Digestive system:Fecal'
        biome_name = 'Fecal'
        #
        mock_study_dir.return_value = "2019/09/ERP117125"
        mock_db.return_value = mock_ena_run_study()
        #
        insert_biome(422, biome_name, 841, 844, 5, lineage)

        with mock_db, mock_study_dir:
            cmd = Command()
            cmd.run_from_argv(
                argv=['manage.py', 'import_study', accession, lineage])
            actual_study = emg_models.Study.objects.get(secondary_accession=accession)
            expected = mock_ena_run_study()
            assert actual_study.secondary_accession == expected.study_id
            assert actual_study.project_id == expected.project_id
            assert actual_study.centre_name == expected.center_name
            assert actual_study.experimental_factor == None
            assert actual_study.is_public == True
            assert actual_study.public_release_date == None
            assert actual_study.study_abstract == expected.study_description
            assert actual_study.study_name == expected.study_title
            assert actual_study.study_status == 'FINISHED'
            assert actual_study.data_origination == 'SUBMITTED'
            assert actual_study.author_email == None
            assert actual_study.author_name == None
            assert actual_study.last_update.strftime("%m/%d/%Y") == timezone.now().strftime("%m/%d/%Y")
            assert actual_study.submission_account_id == expected.submission_account_id
            assert actual_study.biome.biome_name == biome_name
            assert actual_study.result_directory == mock_study_dir.return_value
            assert actual_study.first_created.strftime("%Y-%m-%d %H:%M:%S") == expected.first_created
            assert len(actual_study.publications.all()) == 0
            assert len(actual_study.samples.all()) == 0
