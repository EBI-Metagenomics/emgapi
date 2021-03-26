import os

import pytest
from django.test import TransactionTestCase

from emgapi import models as emg_models
from emgapianns.management.commands.import_sample import Command
from test_utils.emg_fixtures import *  # noqa

# Integrations tests requiring access to the ERAPRO database and emg_backlog_2 on prod database
# To test, add these to the config.yaml file under the db names 'ena' and 'backlog_prod'


@pytest.mark.django_db
@pytest.mark.skipif(('TRAVIS' in os.environ and os.environ['TRAVIS'] == 'true') or ('CI' in os.environ and os.environ['CI'] == 'true'),
                    reason='Skipping this test on Travis CI as internal databases are '
                           'required for full integration tests')
class TestImportSample(TransactionTestCase):
    @pytest.mark.usefixtures('biome')
    @pytest.mark.usefixtures('var_names')
    def test_import_sample_should_load_sample(self):
        accession = 'ERS1282031'
        cmd = Command()
        cmd.run_from_argv(argv=['manage.py', 'import_sample', accession, '--biome', 'root:foo:bar'])
        created_sample = emg_models.Sample.objects.get(accession=accession)

        assert created_sample.primary_accession
        assert created_sample.sample_desc
        assert created_sample.sample_alias
        assert created_sample.sample_name
        assert created_sample.is_public
        assert created_sample.biome == emg_models.Biome.objects.get(lineage='root:foo:bar')

        annotations = emg_models.SampleAnn.objects.filter(sample=created_sample)
        assert annotations.get(var__var_name='host scientific name').var_val_ucv == 'Homo sapiens'
        assert annotations.get(var__var_name='host taxid').var_val_ucv == '9606'
