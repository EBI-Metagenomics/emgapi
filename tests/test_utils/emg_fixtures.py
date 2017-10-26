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

from django.conf import settings

from emgapi import models as emg_models


@pytest.fixture
def api_version():
    return "v%s" % settings.REST_FRAMEWORK['DEFAULT_VERSION']


@pytest.fixture
def biome():
    return emg_models.Biome.objects.create(
        biome_id=1,
        biome_name="bar",
        lft=0, rgt=1, depth=2,
        lineage="root:foo:bar",
    )


@pytest.fixture
def studies(biome):
    studies = []
    for pk in range(1, 50):
        studies.append(
            emg_models.Study(
                biome=biome,
                study_id=pk,
                accession="SRP0{:0>3}".format(pk),
                centre_name="Centre Name",
                is_public=1,
                public_release_date=None,
                study_name="Example study name %i" % pk,
                study_status="FINISHED",
                data_origination="HARVESTED",
                submission_account_id="User-123",
                result_directory="2017/05/SRP{:0>3}".format(pk),
                last_update="1970-01-01 00:00:00",
                first_created="1970-01-01 00:00:00",
                project_id="PRJDB0{:0>3}".format(pk),
            )
        )
    return emg_models.Study.objects.bulk_create(studies)


@pytest.fixture
def samples(biome, studies):
    samples = []
    for s in studies:
        pk = s.study_id
        samples.append(
            emg_models.Sample(
                biome=biome,
                sample_id=pk,
                accession="ERS0{:0>3}".format(pk),
                is_public=1,
                species="homo sapiense",
                sample_name="Example sample name %i" % pk,
                latitude=12.3456,
                longitude=456.456,
                last_update="1970-01-01 00:00:00",
                geo_loc_name="INSTITUTE",
            )
        )
    samples = emg_models.Sample.objects.bulk_create(samples)
    rels = list()
    for st, sm in zip(studies, samples):
        rels.append(emg_models.StudySample(study=st, sample=sm))
    emg_models.StudySample.objects.bulk_create(rels)
    return samples


@pytest.fixture
def study(biome):
    return emg_models.Study.objects.create(
        biome=biome,
        study_id=1234,
        accession="SRP01234",
        centre_name="Centre Name",
        is_public=1,
        public_release_date=None,
        study_name="Example study name SRP01234",
        study_abstract="abcdefghijklmnoprstuvwyz",
        study_status="FINISHED",
        data_origination="HARVESTED",
        submission_account_id="User-123",
        result_directory="2017/05/SRP01234",
        last_update="1970-01-01 00:00:00",
        first_created="1970-01-01 00:00:00",
        project_id="PRJDB1234",
    )


@pytest.fixture
def study_private(biome):
    return emg_models.Study.objects.create(
        biome=biome,
        study_id=222,
        accession="SRP00000",
        centre_name="Centre Name",
        is_public=0,
        public_release_date=None,
        study_name="Example study name SRP00000",
        study_abstract="00000",
        study_status="FINISHED",
        data_origination="HARVESTED",
        submission_account_id="User-123",
        result_directory="2017/05/SRP00000",
        last_update="1970-01-01 00:00:00",
        first_created="1970-01-01 00:00:00",
        project_id="PRJDB0000",
    )


@pytest.fixture
def sample(biome, study):
    sample = emg_models.Sample(
        biome=biome,
        pk=111,
        accession="ERS01234",
        primary_accession="SAMS01234",
        is_public=1,
        species="homo sapiense",
        sample_name="Example sample name ERS01234",
        sample_desc="abcdefghijklmnoprstuvwyz",
        latitude=12.3456,
        longitude=456.456,
        last_update="1970-01-01 00:00:00",
        analysis_completed="1970-01-01",
        collection_date="1970-01-01",
        environment_feature="abcdef",
        environment_material="abcdef",
        geo_loc_name="Geo Location",
        sample_alias="ERS01234",
    )
    sample.save()
    rel = emg_models.StudySample(study=study, sample=sample)
    rel.save()
    return sample


@pytest.fixture
def sample_private(biome, study):
    sample = emg_models.Sample(
        biome=biome,
        pk=222,
        accession="ERS00000",
        primary_accession="SAMS00000",
        is_public=0,
        species="homo sapiense",
        sample_name="Example sample name ERS00000",
        sample_desc="abcdefghijklmnoprstuvwyz",
        latitude=12.3456,
        longitude=456.456,
        last_update="1970-01-01 00:00:00",
        analysis_completed="1970-01-01",
        collection_date="1970-01-01",
        environment_feature="abcdef",
        environment_material="abcdef",
        geo_loc_name="INSTITUTE",
        sample_alias="ERS00000",
    )
    sample.save()
    rel = emg_models.StudySample(study=study, sample=sample)
    rel.save()
    return sample


@pytest.fixture
def analysis_status():
    return emg_models.AnalysisStatus.objects.create(
        pk=3,
        analysis_status='3',
    )


@pytest.fixture
def pipeline():
    return emg_models.Pipeline.objects.create(
        pk=1,
        release_version="1.0",
        release_date="1970-01-01",
    )


@pytest.fixture
def pipelines():
    pipeline_version = [1, 2]
    pipeliens = list()
    for pipe in pipeline_version:
        pipeliens.append(
            emg_models.Pipeline(
                pk=pipe,
                release_version="%d.0" % pipe,
                release_date="1970-01-01",
            )
        )
    return emg_models.Pipeline.objects.bulk_create(pipeliens)


@pytest.fixture
def experiment_type():
    return emg_models.ExperimentType.objects.create(
        pk=1,
        experiment_type="metagenomic"
    )


@pytest.fixture
def runs(study, samples, analysis_status, pipeline, experiment_type):
    jobs = []
    for s in samples:
        pk = s.sample_id
        jobs.append(
            emg_models.AnalysisJob(
                sample=s,
                study=study,
                accession="ABC_{:0>3}".format(pk),
                secondary_accession="DEF_{:0>3}".format(pk),
                run_status_id=4,
                experiment_type=experiment_type,
                pipeline=pipeline,
                analysis_status=analysis_status,
                input_file_name="ABC_FASTQ",
                result_directory="path/version_1.0/ABC_FASTQ",
                submit_time="1970-01-01 00:00:00",
            )
        )
    return emg_models.AnalysisJob.objects.bulk_create(jobs)


@pytest.fixture
def run(study, sample, analysis_status, pipeline, experiment_type):
    return emg_models.AnalysisJob.objects.create(
        job_id=1234,
        accession="ABC01234",
        sample=sample,
        study=study,
        run_status_id=4,
        experiment_type=experiment_type,
        pipeline=pipeline,
        analysis_status=analysis_status,
        input_file_name="ABC_FASTQ",
        result_directory="path/version_1.0/ABC_FASTQ",
        submit_time="1970-01-01 00:00:00",
    )


@pytest.fixture
def run_emptyresults(study, sample, analysis_status, pipeline,
                     experiment_type):
    return emg_models.AnalysisJob.objects.create(
        job_id=1234,
        accession="EMPTY_ABC01234",
        sample=sample,
        study=study,
        run_status_id=4,
        experiment_type=experiment_type,
        pipeline=pipeline,
        analysis_status=analysis_status,
        input_file_name="EMPTY_ABC_FASTQ",
        result_directory="emptypath/version_1.0/EMPTY_ABC_FASTQ",
        submit_time="1970-01-01 00:00:00",
    )


@pytest.fixture
def run_with_sample(study, sample, analysis_status, pipeline, experiment_type):
    return emg_models.AnalysisJob.objects.create(
        job_id=1234,
        accession="ABC01234",
        run_status_id=4,
        sample=sample,
        study=study,
        experiment_type=experiment_type,
        pipeline=pipeline,
        analysis_status=analysis_status,
        input_file_name="ABC_FASTQ",
        result_directory="path/version_1.0/ABC_FASTQ",
        submit_time="1970-01-01 00:00:00",
    )


@pytest.fixture
def analysis_results(study, sample, analysis_status, experiment_type,
                     pipelines):
    res = dict()
    for pipe in pipelines:
        v = "%s.0" % pipe.pk
        res[v] = emg_models.AnalysisJob.objects.create(
            accession="ABC01234",
            study=study,
            sample=sample,
            run_status_id=4,
            experiment_type=experiment_type,
            pipeline=pipe,
            analysis_status=analysis_status,
            input_file_name="ABC_FASTQ",
            result_directory="path/version_%s/ABC_FASTQ" % v,
            submit_time="1970-01-01 00:00:00",
        )
    return res
