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
import os
import sys

from django.core.management import call_command

# import fixtures
from test_utils.emg_fixtures import *  # noqa


@pytest.mark.skipif(sys.version_info < (3, 6),
                    reason="requires Python 3.6")
@pytest.mark.usefixtures('mongodb')
@pytest.mark.django_db
class TestExamples(object):

    def test_list(self, live_server, runs, api_version):
        """
        List samples and its metadata for given study
        """

        from jsonapi_client import Session

        api_base = '%s/%s/' % (live_server.url, api_version)
        with Session(api_base) as s:
            study = s.get('studies', 'SRP0025').resource
            assert study.accession == 'SRP0025'
            # list samples
            sample_list = study.samples
            assert len(sample_list) == 1
            for sample in sample_list:
                # list runs
                run_list = sample.runs
                assert len(run_list) == 1
                for run in run_list:
                    print(
                        study.accession,
                        study.bioproject,
                        sample.accession,
                        sample.biome.biome_name,
                        run.accession,
                        run.experiment_type,
                    )

    def test_annotations(self, live_server, run_with_sample, api_version):
        from jsonapi_client import Session

        call_command('import_summary', 'ABC01234',
                     os.path.dirname(os.path.abspath(__file__)),
                     suffix='.go_slim')

        api_base = '%s/%s/' % (live_server.url, api_version)
        with Session(api_base) as s:
            run = s.get('runs', 'ABC01234').resource
            for analysis in run.analysis:
                go_terms = []
                for go in analysis.go_slim:
                    go_terms.append(go.accession)
                expected = ['GO:0030246', 'GO:0046906', 'GO:0043167']
                assert go_terms == expected
