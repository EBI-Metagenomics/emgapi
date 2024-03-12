import os

import pytest
from django.core.management import call_command

from test_utils.emg_fixtures import *  # noqa

@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("experiment_type")
class TestEbiSearchDump:
    def test_dump_studies(self, sample):
        """Test ebi search dump studies"""
        call_command(
            "ebi_search_study_dump", "-o", f"/tmp/emg_dump_studies",
        )
        assert os.path.exists(f"/tmp/emg_dump_studies/projects.xml")
        assert os.path.isfile(f"/tmp/emg_dump_studies/projects.xml")
        assert os.path.exists(f"/tmp/emg_dump_studies/projects-deletes.xml")
        assert os.path.isfile(f"/tmp/emg_dump_studies/projects-deletes.xml")

        with open(f"/tmp/emg_dump_studies/projects.xml") as f:
            dump = f.read()
            assert "MGYS00001234" in dump
            assert "<entry_count>1</entry_count>" in dump

        with open(f"/tmp/emg_dump_studies/projects-deletes.xml") as f:
            dump = f.readlines()
            assert len(dump) == 5  # i.e. no entries within the xml

    def test_dump_analyses(self, run_v5):
        """Test ebi search dump analyses"""
        call_command(
            "ebi_search_analysis_dump", "-o", f"/tmp/emg_dump_analyses",
        )
        assert os.path.exists(f"/tmp/emg_dump_analyses/analyses_0001.xml")
        assert os.path.isfile(f"/tmp/emg_dump_analyses/analyses_0001.xml")
        assert os.path.exists(f"/tmp/emg_dump_analyses/analyses-deletes.xml")
        assert os.path.isfile(f"/tmp/emg_dump_analyses/analyses-deletes.xml")

        with open(f"/tmp/emg_dump_analyses/analyses_0001.xml") as f:
            dump = f.read()
            assert "MGYA00001234" in dump
            assert "<entry_count>1</entry_count>" in dump

        with open(f"/tmp/emg_dump_analyses/analyses-deletes.xml") as f:
            dump = f.readlines()
            assert len(dump) == 5  # i.e. no entries within the xml

