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

from model_mommy import mommy

from emgapi import models as emg_models


@pytest.fixture
def biome():
    b = mommy.make(
        'emgapi.Biome',
        biome_name="bar",
        lineage="root:foo:bar",
        pk=123)
    return b


@pytest.fixture
def studies(biome):
    studies = []
    for pk in range(1, 100):
        studies.append(
            mommy.prepare(
                'emgapi.Study',
                biome=biome,
                pk=pk,
                accession="SRP0{:0>3}".format(pk),
                centre_name="Centre Name",
                is_public=1,
                public_release_date=None,
                study_name="Example study name %i" % pk,
                study_status="FINISHED",
                data_origination="HARVESTED",
                submission_account_id="User-123",
                result_directory="2017/05/SRP{:0>3}".format(pk),
                project_id="PRJDB0{:0>3}".format(pk)
            )
        )
    return emg_models.Study.objects.bulk_create(studies)


@pytest.fixture
def samples(biome, studies):
    samples = []
    for s in studies:
        pk = s.pk
        samples.append(
            mommy.prepare(
                'emgapi.Sample',
                biome=biome,
                pk=pk,
                study_id=pk,
                accession="ERS0{:0>3}".format(pk),
                is_public=1,
                species="homo sapiense",
                sample_name="Example sample name %i" % pk,
                latitude=123.123,
                longitude=456.456,
                geo_loc_name="INSTITUTE"
            )
        )
    return emg_models.Sample.objects.bulk_create(samples)


@pytest.fixture
def analysis_status():
    a = mommy.make(
        'emgapi.AnalysisStatus',
        pk=3,
        analysis_status='3')
    return a


@pytest.fixture
def pipeline():
    p = mommy.make(
        'emgapi.Pipeline',
        pk=1,
        release_version="1.0")
    return p


@pytest.fixture
def experiment_type():
    et = mommy.make(
        'emgapi.ExperimentType',
        pk=1,
        experiment_type="metagenomic")
    return et


@pytest.fixture
def runs(samples, analysis_status, pipeline, experiment_type):
    jobs = []
    for s in samples:
        pk = s.pk
        jobs.append(
            mommy.prepare(
                'emgapi.AnalysisJob',
                pk=pk,
                sample_id=pk,
                accession="ABC_{:0>3}".format(pk),
                run_status_id=4,
                experiment_type_id=experiment_type.pk,
                pipeline_id=pipeline.pk,
                analysis_status_id=analysis_status.pk,
                input_file_name="ABC_FASTQ",
                result_directory="path/version_1.0/ABC_FASTQ",
            )
        )
    return emg_models.AnalysisJob.objects.bulk_create(jobs)
