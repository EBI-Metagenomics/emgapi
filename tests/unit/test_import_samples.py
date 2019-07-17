import mock

import pytest
from emgapianns.management.commands.import_sample import Command
from emgena import models as ena_models
from emgapi import models as emg_models
from test_utils.emg_fixtures import *  # noqa
from django.test import TransactionTestCase


def mock_fetch_sample_api(*args, **kwargs):
    return {
        'sample_accession': 'SAMEA4370582',
        'secondary_sample_accession': 'ERS1282031',
        'description': 'Example description',
        'collection_date': '2019-01-01',
        'status_id': '4',
        'environment_biome': '',
        'environment_feature': '',
        'environment_material': '',
        'sample_alias': 'Test sample alias',
        'host_tax_id': '',
        'last_update': '2019-01-01',
        'location': '44 N 53 E'
    }


def create_model(*args, **kwargs):
    sample = ena_models.Sample()
    sample.submission_account_id = 'Webin-460'
    return sample


@pytest.mark.django_db
class TestImportSampleTransactions(TransactionTestCase):
    @pytest.mark.usefixtures("biome")
    @pytest.mark.usefixtures("var_names")
    def test_import_sample_should_load_sample(self):
        sample_accession = 'ERS1282031'
        mock_api_data = mock_fetch_sample_api()
        mock_api = mock.patch.object(Command, 'fetch_sample_api', new=lambda *args, **kwargs: mock_api_data)
        mock_db = mock.patch.object(Command, 'fetch_sample_ena_db', new=create_model)
        with mock_api, mock_db:
            cmd = Command()
            cmd.run_from_argv(argv=['manage.py', 'import_sample', sample_accession, '--biome', 'root:foo:bar'])
            created_sample = emg_models.Sample.objects.get(accession=sample_accession)
            expected_data = mock_fetch_sample_api()
            assert created_sample.accession == expected_data['secondary_sample_accession']
            assert created_sample.primary_accession == expected_data['sample_accession']
            assert created_sample.sample_desc == expected_data['description']
            assert created_sample.sample_alias == expected_data['sample_alias']
            assert created_sample.sample_name == expected_data['sample_alias']
            assert created_sample.is_public
            assert created_sample.biome == emg_models.Biome.objects.get(lineage='root:foo:bar')

    @pytest.mark.usefixtures("biome")
    @pytest.mark.usefixtures("var_names")
    def test_import_sample_should_load_private_sample(self):
        sample_accession = 'ERS1282031'
        mock_api_data = mock_fetch_sample_api()
        mock_api_data['status_id'] = '2'
        mock_api = mock.patch.object(Command, 'fetch_sample_api', new=lambda *args, **kwargs: mock_api_data)
        mock_db = mock.patch.object(Command, 'fetch_sample_ena_db', new=create_model)
        with mock_api, mock_db:
            cmd = Command()
            cmd.run_from_argv(argv=['manage.py', 'import_sample', sample_accession, '--biome', 'root:foo:bar'])
            created_sample = emg_models.Sample.objects.get(accession=sample_accession)
            assert not created_sample.is_public

    @pytest.mark.usefixtures("biome")
    @pytest.mark.usefixtures("var_names")
    def test_import_sample_should_not_load_location(self):
        sample_accession = 'ERS1282031'
        mock_api_data = mock_fetch_sample_api()
        del mock_api_data['location']
        mock_api = mock.patch.object(Command, 'fetch_sample_api', new=lambda *args, **kwargs: mock_api_data)
        mock_db = mock.patch.object(Command, 'fetch_sample_ena_db', new=create_model)
        with mock_api, mock_db:
            cmd = Command()
            cmd.run_from_argv(argv=['manage.py', 'import_sample', sample_accession, '--biome', 'root:foo:bar'])
            created_sample = emg_models.Sample.objects.get(accession=sample_accession)
            assert created_sample.latitude is None
            assert created_sample.longitude is None

    @pytest.mark.usefixtures("biome")
    @pytest.mark.usefixtures("var_names")
    def test_import_sample_should_load_location(self):
        sample_accession = 'ERS1282031'
        mock_api_data = mock_fetch_sample_api()
        mock_api = mock.patch.object(Command, 'fetch_sample_api', new=lambda *args, **kwargs: mock_api_data)
        mock_db = mock.patch.object(Command, 'fetch_sample_ena_db', new=create_model)
        with mock_api, mock_db:
            cmd = Command()
            cmd.run_from_argv(argv=['manage.py', 'import_sample', sample_accession, '--biome', 'root:foo:bar'])
            created_sample = emg_models.Sample.objects.get(accession=sample_accession)
            assert created_sample.latitude == 44.0
            assert created_sample.longitude == 53.0
