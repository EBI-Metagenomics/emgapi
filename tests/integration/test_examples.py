#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2017 EMBL - European Bioinformatics Institute
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

import pytest

import sys

# import fixtures
from test_utils.emg_fixtures import *  # noqa


@pytest.mark.skipif(sys.version_info < (3, 6),
                    reason="requires Python 3.6")
@pytest.mark.django_db
def test_list_samples(live_server, runs):
    """
    List samples and its metadata for given study
    """

    from jsonapi_client import Session

    with Session('%s/api/' % live_server.url) as s:
        study = s.get('studies', 'SRP0025').resource
        assert study.accession == 'SRP0025'
        # list samples
        sample_list = study.samples
        assert len(sample_list) == 1
        for sample in study.samples:
            # list runs
            run_list = sample.relationships.runs.fetch()
            assert len(run_list) == 1
            for run in run_list:
                print(
                    study.accession,
                    sample.accession,
                    run.accession, run['pipeline_version'],
                    run['result_directory'], run['input_file_name']
                )
