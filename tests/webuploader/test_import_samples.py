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

from unittest import mock

import pytest

from emgapi import models as emg_models
from emgapianns.management.commands.import_sample import Command
from emgena import models as ena_models
from test_utils.emg_fixtures import *  # noqa


def mock_fetch_sample_api(*args, **kwargs):
    return {
        'sample_accession': 'SAMEA4370582',
        'secondary_sample_accession': 'ERS1282031',
        'description': 'Example description',
        'collection_date': '2019-01-01',
        'status': 'public',
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


@pytest.mark.django_db(transaction=True)
class TestImportSampleTransactions:

    @pytest.mark.usefixtures("biome")
    @pytest.mark.usefixtures("var_names")
    def test_import_sample_should_load_sample(self):
        sample_accession = 'ERS1282031'
        mock_api_data = mock_fetch_sample_api()
        mock_api = mock.patch.object(Command, 'fetch_sample_api', new=lambda *args, **kwargs: mock_api_data)
        mock_db = mock.patch.object(Command, 'get_ena_db_sample', new=create_model)
        mock_api_sample_studies = mock.patch.object(
            Command,
            'get_sample_studies',
            new=lambda *args, **kwargs: {'ERP022699'}
        )
        with mock_api, mock_db, mock_api_sample_studies:
            cmd = Command()
            cmd.run_from_argv(argv=['manage.py', 'import_sample', sample_accession, '--biome', 'root:foo:bar'])
            created_sample = emg_models.Sample.objects.get(accession=sample_accession)
            expected_data = mock_fetch_sample_api()
            assert created_sample.accession == expected_data['secondary_sample_accession']
            assert created_sample.primary_accession == expected_data['sample_accession']
            assert created_sample.sample_desc == expected_data['description']
            assert created_sample.sample_alias == expected_data['sample_alias']
            assert created_sample.sample_name == expected_data['sample_alias']
            assert created_sample.is_private == False
            assert created_sample.biome == emg_models.Biome.objects.get(lineage='root:foo:bar')

    @pytest.mark.usefixtures("biome")
    @pytest.mark.usefixtures("var_names")
    def test_import_sample_should_load_private_sample(self):
        sample_accession = 'ERS1282031'
        mock_api_data = mock_fetch_sample_api()
        mock_api_data['status'] = 'private'
        mock_api = mock.patch.object(Command, 'fetch_sample_api', new=lambda *args, **kwargs: mock_api_data)
        mock_db = mock.patch.object(Command, 'get_ena_db_sample', new=create_model)
        mock_api_sample_studies = mock.patch.object(
            Command,
            'get_sample_studies',
            new=lambda *args, **kwargs: {'ERP022699'}
        )
        with mock_api, mock_db, mock_api_sample_studies:
            cmd = Command()
            cmd.run_from_argv(argv=['manage.py', 'import_sample', sample_accession, '--biome', 'root:foo:bar'])
            created_sample = emg_models.Sample.objects.get(accession=sample_accession)
            assert created_sample.is_private

    @pytest.mark.usefixtures("biome")
    @pytest.mark.usefixtures("var_names")
    def test_import_sample_should_not_load_location_if_empty_api_field(self):
        sample_accession = 'ERS1282031'
        mock_api_data = mock_fetch_sample_api()
        del mock_api_data['location']
        mock_api = mock.patch.object(Command, 'fetch_sample_api', new=lambda *args, **kwargs: mock_api_data)
        mock_db = mock.patch.object(Command, 'get_ena_db_sample', new=create_model)
        mock_api_sample_studies = mock.patch.object(
            Command,
            'get_sample_studies',
            new=lambda *args, **kwargs: {'ERP022699'}
        )
        with mock_api, mock_db, mock_api_sample_studies:
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
        mock_db = mock.patch.object(Command, 'get_ena_db_sample', new=create_model)
        mock_api_sample_studies = mock.patch.object(
            Command,
            'get_sample_studies',
            new=lambda *args, **kwargs: {'ERP022699'}
        )
        with mock_api, mock_db, mock_api_sample_studies:
            cmd = Command()
            cmd.run_from_argv(argv=['manage.py', 'import_sample', sample_accession, '--biome', 'root:foo:bar'])
            created_sample = emg_models.Sample.objects.get(accession=sample_accession)
            assert created_sample.latitude == 44.0
            assert created_sample.longitude == 53.0

    @pytest.mark.usefixtures("biome")
    @pytest.mark.usefixtures("var_names")
    def test_import_sample_should_load_var_names(self):
        sample_accession = 'ERS1282031'
        mock_api_data = mock_fetch_sample_api()
        mock_api = mock.patch.object(Command, 'fetch_sample_api', new=lambda *args, **kwargs: mock_api_data)
        mock_db = mock.patch.object(Command, 'get_ena_db_sample', new=create_model)
        mock_api_sample_studies = mock.patch.object(
            Command,
            'get_sample_studies',
            new=lambda *args, **kwargs: {'ERP022699'}
        )
        with mock_api, mock_db, mock_api_sample_studies:
            cmd = Command()
            cmd.run_from_argv(argv=['manage.py', 'import_sample', sample_accession, '--biome', 'root:foo:bar'])
            created_sample = emg_models.Sample.objects.get(accession=sample_accession)
            annotations = emg_models.SampleAnn.objects.filter(sample=created_sample)
            assert annotations.get(var__var_name='geographic location (latitude)').var_val_ucv == '44.0'
            assert annotations.get(var__var_name='geographic location (longitude)').var_val_ucv == '53.0'
            assert annotations.get(var__var_name='collection date').var_val_ucv == '2019-01-01'

    @pytest.mark.usefixtures("biome_human")
    @pytest.mark.usefixtures("var_names")
    def test_import_sample_should_tag_species(self):
        sample_accession = 'ERS1282031'
        mock_api_data = mock_fetch_sample_api()
        del mock_api_data['location']
        mock_api = mock.patch.object(Command, 'fetch_sample_api', new=lambda *args, **kwargs: mock_api_data)
        mock_db = mock.patch.object(Command, 'get_ena_db_sample', new=create_model)
        mock_api_sample_studies = mock.patch.object(
            Command,
            'get_sample_studies',
            new=lambda *args, **kwargs: {'ERP022699'}
        )
        with mock_api, mock_db, mock_api_sample_studies:
            cmd = Command()
            cmd.run_from_argv(
                argv=['manage.py', 'import_sample', sample_accession, '--biome', 'root:Host-associated:Human'])
            created_sample = emg_models.Sample.objects.get(accession=sample_accession)
            assert created_sample.species == 'Homo sapiens'
            assert created_sample.host_tax_id == 9606

    @pytest.mark.usefixtures("biome")
    @pytest.mark.usefixtures("var_names")
    def test_import_sample_should_tag_no_species(self):
        sample_accession = 'ERS1282031'
        mock_api_data = mock_fetch_sample_api()
        del mock_api_data['location']
        mock_api = mock.patch.object(Command, 'fetch_sample_api', new=lambda *args, **kwargs: mock_api_data)
        mock_db = mock.patch.object(Command, 'get_ena_db_sample', new=create_model)
        mock_api_sample_studies = mock.patch.object(
            Command,
            'get_sample_studies',
            new=lambda *args, **kwargs: {'ERP022699'}
        )
        with mock_api, mock_db, mock_api_sample_studies:
            cmd = Command()
            cmd.run_from_argv(
                argv=['manage.py', 'import_sample', sample_accession, '--biome', 'root:foo:bar'])
            created_sample = emg_models.Sample.objects.get(accession=sample_accession)
            assert created_sample.species is None
            assert created_sample.host_tax_id is None

    @pytest.mark.usefixtures("biome")
    @pytest.mark.usefixtures("var_names")
    def test_import_sample_should_tag_to_study(self):
        sample_accession = 'ERS1282031'
        fake_study = 'ERP001736'
        mock_api_data = mock_fetch_sample_api()
        mock_api = mock.patch.object(Command, 'fetch_sample_api', new=lambda *args, **kwargs: mock_api_data)
        mock_db = mock.patch.object(Command, 'get_ena_db_sample', new=create_model)

        s = emg_models.Study(secondary_accession=fake_study,
                             is_private=False,
                             last_update='2019-01-01',
                             first_created='2019-01-01',
                             biome=emg_models.Biome.objects.get(lineage='root:foo:bar'))
        s.save()
        mock_api_studies = mock.patch.object(Command, 'get_sample_studies', new=lambda *args, **kwargs: {fake_study})
        with mock_api, mock_db, mock_api_studies:
            cmd = Command()
            cmd.run_from_argv(argv=['manage.py', 'import_sample', sample_accession, '--biome', 'root:foo:bar'])
            created_sample = emg_models.Sample.objects.get(accession=sample_accession)
            assert emg_models.StudySample.objects.get(study=s, sample=created_sample)

    @pytest.mark.usefixtures("biome")
    @pytest.mark.usefixtures("var_names")
    def test_import_sample_duplicate_import_should_not_duplicate_objects(self):
        sample_accession = 'ERS1282031'
        fake_study = 'ERP001736'
        mock_api_data = mock_fetch_sample_api()
        mock_api = mock.patch.object(Command, 'fetch_sample_api', new=lambda *args, **kwargs: mock_api_data)
        mock_db = mock.patch.object(Command, 'get_ena_db_sample', new=create_model)

        s = emg_models.Study(secondary_accession=fake_study,
                             is_private=False,
                             last_update='2019-01-01',
                             first_created='2019-01-01',
                             biome=emg_models.Biome.objects.get(lineage='root:foo:bar'))
        s.save()
        mock_api_studies = mock.patch.object(Command, 'get_sample_studies', new=lambda *args, **kwargs: {fake_study})
        with mock_api, mock_db, mock_api_studies:
            cmd = Command()
            cmd.run_from_argv(argv=['manage.py', 'import_sample', sample_accession, '--biome', 'root:foo:bar'])
            cmd.run_from_argv(argv=['manage.py', 'import_sample', sample_accession, '--biome', 'root:foo:bar'])
            created_sample = emg_models.Sample.objects.get(accession=sample_accession)
            assert len(emg_models.StudySample.objects.filter(study=s, sample=created_sample)) == 1
            assert len(emg_models.Sample.objects.filter(accession=sample_accession)) == 1
            assert len(emg_models.SampleAnn.objects.filter(sample=created_sample)) == 3

    @pytest.mark.usefixtures("biome")
    def test_import_should_fail_if_varnames_missing(self):
        sample_accession = 'ERS1282031'
        mock_api_data = mock_fetch_sample_api()
        mock_api = mock.patch.object(Command, 'fetch_sample_api', new=lambda *args, **kwargs: mock_api_data)
        mock_db = mock.patch.object(Command, 'get_ena_db_sample', new=create_model)
        mock_api_sample_studies = mock.patch.object(
            Command,
            'get_sample_studies',
            new=lambda *args, **kwargs: {'ERP022699'}
        )
        with mock_api, mock_db, mock_api_sample_studies:
            cmd = Command()
            with pytest.raises(emg_models.VariableNames.DoesNotExist):
                cmd.run_from_argv(argv=['manage.py', 'import_sample', sample_accession, '--biome', 'root:foo:bar'])
