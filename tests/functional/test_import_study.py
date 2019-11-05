from unittest.mock import patch

import mock
import pytest
from test_utils.emg_fixtures import *  # noqa

from emgapi import models as emg_models
from emgapianns.management.commands.import_study import Command
from emgapianns.management.lib.create_or_update_study import StudyImporter
from emgena import models as ena_models


def mock_fetch_ena_study_api(*args, **kwargs):
    return {
        'study_id': 'ERP117125',
        'project_id': 'PRJEB34249',
        'study_status': 'public',
        'center_name': 'UNIVERSITY OF CAMBRIDGE',
        'hold_date': None,
        'first_created': '2019-09-04 11:23:26',
        'last_updated': '2019-09-04 11:23:26',
        'study_title': 'Dysbiosis associated with acute helminth infections in herbivorous youngstock - '
                       'observations and implications',
        'study_description': 'This study investigates, for the first time, the associations between acute '
                             'infections by GI helminths and the faecal microbial and metabolic profiles of '
                             'a cohort of equine youngstock, prior to and following treatment with '
                             'parasiticides (ivermectin).',
        'submission_account_id': 'Webin-50804',
        'pubmed_id': ''
    }


def create_model(*args, **kwargs):
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


@pytest.mark.django_db
class TestImportStudyTransactions:

    @pytest.mark.usefixtures("biome")
    @pytest.mark.usefixtures("var_names")
    @pytest.mark.parametrize("accession, lineage", [
        ('ERP117125', 'root:Host-associated:Mammals:Digestive system:Fecal')
    ])
    @patch('emgapianns.management.commands.import_study.Command.get_study_dir')
    @patch('emgapianns.management.lib.create_or_update_study.StudyImporter._fetch_study_metadata')
    def test_import_study_should_succeed(self, mock_db, mock_study_dir, accession, lineage):
        mock_study_dir.return_value = "2019/09/ERP117125"
        mock_db.return_value = create_model()
        # mock_db = mock.patch.object(StudyImporter, '_fetch_study_metadata', new=create_model)
        with mock_db, mock_study_dir:
            cmd = Command()
            cmd.run_from_argv(
                argv=['manage.py', 'import_study', accession, lineage])
            created_study = emg_models.Study.objects.get(secondary_accession=accession)
            expected_data = mock_fetch_ena_study_api()
            assert created_study.accession == expected_data['secondary_sample_accession']
            assert created_study.primary_accession == expected_data['sample_accession']
            assert created_study.sample_desc == expected_data['description']
            assert created_study.sample_alias == expected_data['sample_alias']
            assert created_study.sample_name == expected_data['sample_alias']
            assert created_study.is_public
            assert created_study.biome == emg_models.Biome.objects.get(lineage='root:foo:bar')
