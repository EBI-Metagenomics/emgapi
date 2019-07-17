import pytest
from django.test import TransactionTestCase
from emgapianns.management.commands.import_sample import Command
import os
from test_utils.emg_fixtures import *  # noqa

# Integrations tests requiring access to the ERAPRO database and emg_backlog_2 on prod database
# To test, add these to the config.yaml file under the db names 'ena' and 'backlog_prod'


@pytest.mark.django_db
@pytest.mark.skipif("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true", reason="Skipping this test on Travis CI."
                                                                                      " as internal databases are "
                                                                                      "required for full integration "
                                                                                      "tests")
class TestImportSample(TransactionTestCase):
    @pytest.mark.usefixtures("biome")
    @pytest.mark.usefixtures("var_names")
    def test_import_sample_should_load_sample(self):
        cmd = Command()
        cmd.run_from_argv(argv=['manage.py', 'import_sample', 'ERS1282031', '--biome', 'root:foo:bar'])
        # TODO check they were inserted!!
