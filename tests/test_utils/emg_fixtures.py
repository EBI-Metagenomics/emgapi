#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 EMBL - European Bioinformatics Institute
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest

from django.conf import settings

from emgapi import models as emg_models

__all__ = ['apiclient', 'api_version', 'biome', 'biome_human', 'super_study', 'studies',
           'samples', 'study', 'study_private', 'sample', 'sample_private',
           'run_status', 'analysis_status',
           'pipeline', 'pipelines', 'experiment_type',
           'runs', 'run', 'run_v5', 'runjob_pipeline_v1', 'run_emptyresults', 'run_with_sample',
           'analysis_results', 'run_multiple_analysis', 'var_names', 'analysis_metadata_variable_names']


@pytest.fixture
def apiclient():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def api_version():
    return 'v{}'.format(settings.REST_FRAMEWORK['DEFAULT_VERSION'])


@pytest.fixture
def biome():
    return emg_models.Biome.objects.create(
        biome_id=1,
        biome_name='bar',
        lft=0, rgt=1, depth=2,
        lineage='root:foo:bar',
    )

@pytest.fixture
def biome_human():
    return emg_models.Biome.objects.create(
        biome_id=1,
        biome_name='Human',
        lft=0, rgt=1, depth=2,
        lineage='root:Host-associated:Human',
    )


@pytest.fixture
def super_study(study, study_private, biome):
    ss = emg_models.SuperStudy.objects.create(
        super_study_id=1,
        title='Human Microbiome',
        description='Just a test description',
    )
    emg_models.SuperStudyBiome.objects.create(biome=biome,
                                              super_study=ss)
    emg_models.SuperStudyStudy.objects.create(study=study,
                                              super_study=ss)
    emg_models.SuperStudyStudy.objects.create(study=study_private,
                                              super_study=ss)
    return ss


@pytest.fixture
def studies(biome):
    studies = []
    for pk in range(1, 50):
        studies.append(
            emg_models.Study(
                biome=biome,
                study_id=pk,
                secondary_accession='SRP0{:0>3}'.format(pk),
                centre_name='Centre Name',
                is_public=1,
                public_release_date=None,
                study_name='Example study name %i' % pk,
                study_status='FINISHED',
                data_origination='HARVESTED',
                submission_account_id='User-123',
                result_directory='2017/05/SRP{:0>3}'.format(pk),
                last_update='1970-01-01 00:00:00',
                first_created='1970-01-01 00:00:00',
                project_id='PRJDB0{:0>3}'.format(pk),
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
                accession='ERS0{:0>3}'.format(pk),
                is_public=1,
                species='homo sapiense',
                sample_name='Example sample name %i' % pk,
                latitude=12.3456,
                longitude=456.456,
                last_update='1970-01-01 00:00:00',
                geo_loc_name='INSTITUTE',
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
        secondary_accession='SRP01234',
        centre_name='Centre Name',
        is_public=1,
        public_release_date=None,
        study_name='Example study name SRP01234',
        study_abstract='abcdefghijklmnoprstuvwyz',
        study_status='FINISHED',
        data_origination='HARVESTED',
        submission_account_id='User-123',
        result_directory='2017/05/SRP01234',
        last_update='1970-01-01 00:00:00',
        first_created='1970-01-01 00:00:00',
        project_id='PRJDB1234',
    )


@pytest.fixture
def study_private(biome):
    return emg_models.Study.objects.create(
        biome=biome,
        study_id=222,
        secondary_accession='SRP00000',
        centre_name='Centre Name',
        is_public=0,
        public_release_date=None,
        study_name='Example study name SRP00000',
        study_abstract='00000',
        study_status='FINISHED',
        data_origination='HARVESTED',
        submission_account_id='User-123',
        result_directory='2017/05/SRP00000',
        last_update='1970-01-01 00:00:00',
        first_created='1970-01-01 00:00:00',
        project_id='PRJDB0000',
    )


@pytest.fixture
def sample(biome, study):
    sample = emg_models.Sample(
        biome=biome,
        pk=111,
        accession='ERS01234',
        primary_accession='SAMS01234',
        is_public=1,
        species='homo sapiense',
        sample_name='Example sample name ERS01234',
        sample_desc='abcdefghijklmnoprstuvwyz',
        latitude=12.3456,
        longitude=456.456,
        last_update='1970-01-01 00:00:00',
        analysis_completed='1970-01-01',
        collection_date='1970-01-01',
        environment_feature='abcdef',
        environment_material='abcdef',
        geo_loc_name='Geo Location',
        sample_alias='ERS01234',
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
        accession='ERS00000',
        primary_accession='SAMS00000',
        is_public=0,
        species='homo sapiense',
        sample_name='Example sample name ERS00000',
        sample_desc='abcdefghijklmnoprstuvwyz',
        latitude=12.3456,
        longitude=456.456,
        last_update='1970-01-01 00:00:00',
        analysis_completed='1970-01-01',
        collection_date='1970-01-01',
        environment_feature='abcdef',
        environment_material='abcdef',
        geo_loc_name='INSTITUTE',
        sample_alias='ERS00000',
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
def run_status():
    status, _ = emg_models.Status.objects.get_or_create(
        pk=4,
        status='public',
    )
    return status


@pytest.fixture
def pipeline(pipelines):
    """Return Pipeline Version 4.1
    """
    return pipelines.filter(release_version='4.1').first()


@pytest.fixture
def pipelines():
    pipeline_version = [1.0, 4.0, 4.1, 5.0]
    i = 1
    for pipe in pipeline_version:
        p, _ = emg_models.Pipeline.objects.get_or_create(
            pk=i,
            release_version=str(pipe),
            release_date='1970-01-01')
        i += 1
    return emg_models.Pipeline.objects.all()


@pytest.fixture
def experiment_type():
    return emg_models.ExperimentType.objects.create(
        pk=1,
        experiment_type='metagenomic'
    )


@pytest.fixture
def runs(study, samples, run_status, analysis_status, pipeline,
         experiment_type):
    jobs = []
    for s in samples:
        pk = s.sample_id
        run, created = emg_models.Run.objects.get_or_create(
            sample=s,
            study=study,
            accession='ABC_{:0>3}'.format(pk),
            secondary_accession='DEF_{:0>3}'.format(pk),
            status_id=run_status,
            experiment_type=experiment_type,
        )
        _aj = emg_models.AnalysisJob(
            sample=s,
            study=study,
            run=run,
            run_status_id=4,
            experiment_type=experiment_type,
            pipeline=pipeline,
            analysis_status=analysis_status,
            input_file_name='ABC_FASTQ',
            result_directory='test_data/version_1.0/ABC_FASTQ',
            submit_time='1970-01-01 00:00:00',
        )
        jobs.append(_aj)
    return emg_models.AnalysisJob.objects.bulk_create(jobs)


@pytest.fixture
def run(study, sample, run_status, analysis_status, pipeline, experiment_type):
    run, _ = emg_models.Run.objects.get_or_create(
        run_id=1234,
        accession='ABC01234',
        sample=sample,
        study=study,
        status_id=run_status,
        experiment_type=experiment_type
    )
    emg_models.AnalysisJob.objects.create(
        job_id=1234,
        sample=sample,
        study=study,
        run=run,
        run_status_id=4,
        experiment_type=experiment_type,
        pipeline=pipeline,
        analysis_status=analysis_status,
        input_file_name='ABC_FASTQ',
        result_directory='test_data/version_1.0/ABC_FASTQ',
        submit_time='1970-01-01 00:00:00'
    )
    return run


@pytest.fixture
def run_v5(study, sample, run_status, analysis_status, pipelines, experiment_type):
    p5 = pipelines.filter(release_version='5.0').first()
    run, _ = emg_models.Run.objects.get_or_create(
        run_id=5555,
        accession='ABC01234',
        sample=sample,
        study=study,
        status_id=run_status,
        experiment_type=experiment_type
    )
    emg_models.AnalysisJob.objects.create(
        job_id=1234,
        sample=sample,
        study=study,
        run=run,
        run_status_id=4,
        experiment_type=experiment_type,
        pipeline=p5,
        analysis_status=analysis_status,
        input_file_name='ABC_FASTQ',
        result_directory='test_data/version_5.0/ABC_FASTQ',
        submit_time='1970-01-01 00:00:00'
    )
    return run


@pytest.fixture
def runjob_pipeline_v1(run, sample, study, experiment_type, analysis_status, pipelines):
    return emg_models.AnalysisJob.objects.create(  # NOQA
        job_id=12345,
        sample=sample,
        study=study,
        run=run,
        run_status_id=4,
        experiment_type=experiment_type,
        pipeline=pipelines.filter(release_version='1.0').first(),
        analysis_status=analysis_status,
        input_file_name='ABC_FASTQ',
        result_directory='test_data/version_1.0/ABC_FASTQ',
        submit_time='1970-01-01 00:00:00'
    )


@pytest.fixture
def run_multiple_analysis(study, sample, run_status, analysis_status,
                          experiment_type):
    pipeline, created = emg_models.Pipeline.objects.get_or_create(
        pk=1,
        release_version='1.0',
        release_date='1970-01-01',
    )
    pipeline4, created4 = emg_models.Pipeline.objects.get_or_create(
        pk=4,
        release_version='4.0',
        release_date='1970-01-01',
    )
    pipeline5, created5 = emg_models.Pipeline.objects.get_or_create(
        pk=5,
        release_version='5.0',
        release_date='2020-01-01',
    )
    run = emg_models.Run.objects.create(
        run_id=1234,
        accession='ABC01234',
        sample=sample,
        study=study,
        status_id=run_status,
        experiment_type=experiment_type
    )
    _anl1 = emg_models.AnalysisJob.objects.create(
        job_id=1234,
        sample=sample,
        study=study,
        run=run,
        run_status_id=4,
        experiment_type=experiment_type,
        pipeline=pipeline,
        analysis_status=analysis_status,
        input_file_name='ABC_FASTQ',
        result_directory='test_data/version_1.0/ABC_FASTQ',
        submit_time='1970-01-01 00:00:00',
    )
    _anl4 = emg_models.AnalysisJob.objects.create(
        job_id=5678,
        sample=sample,
        study=study,
        run=run,
        run_status_id=4,
        experiment_type=experiment_type,
        pipeline=pipeline4,
        analysis_status=analysis_status,
        input_file_name='ABC_FASTQ',
        result_directory='test_data/version_4.0/ABC_FASTQ',
        submit_time='1970-01-01 00:00:00',
    )
    _anl5 = emg_models.AnalysisJob.objects.create(
        job_id=466090,
        sample=sample,
        study=study,
        run=run,
        run_status_id=4,
        experiment_type=experiment_type,
        pipeline=pipeline5,
        analysis_status=analysis_status,
        input_file_name='ABC_FASTQ',
        result_directory='test_data/version_5.0/ABC_FASTQ',
        submit_time='2020-01-01 00:00:00',
    )
    return (_anl1, _anl4, _anl5)


@pytest.fixture
def run_emptyresults(study, sample, run_status, analysis_status, pipeline,
                     experiment_type):
    run = emg_models.Run.objects.create(
        run_id=1234,
        accession='ABC01234',
        sample=sample,
        study=study,
        status_id=run_status,
        experiment_type=experiment_type
    )
    return emg_models.AnalysisJob.objects.create(
        job_id=1234,
        sample=sample,
        study=study,
        run=run,
        run_status_id=4,
        experiment_type=experiment_type,
        pipeline=pipeline,
        analysis_status=analysis_status,
        input_file_name='EMPTY_ABC_FASTQ',
        result_directory='test_data/version_1.0/EMPTY_ABC_FASTQ',
        submit_time='1970-01-01 00:00:00',
    )


@pytest.fixture
def run_with_sample(study, sample, run_status, analysis_status, pipeline,
                    experiment_type):
    run = emg_models.Run.objects.create(
        run_id=1234,
        accession='ABC01234',
        status_id=run_status,
        sample=sample,
        study=study,
        experiment_type=experiment_type,
    )
    return emg_models.AnalysisJob.objects.create(
        job_id=1234,
        sample=sample,
        study=study,
        run=run,
        run_status_id=4,
        experiment_type=experiment_type,
        pipeline=pipeline,
        analysis_status=analysis_status,
        input_file_name='ABC_FASTQ',
        result_directory='test_data/version_1.0/ABC_FASTQ',
        submit_time='1970-01-01 00:00:00'
    )


@pytest.fixture
def analysis_results(study, sample, run_status, analysis_status,
                     experiment_type, pipelines):
    run = emg_models.Run.objects.create(
        run_id=1234,
        accession='ABC01234',
        status_id=run_status,
        sample=sample,
        study=study,
        experiment_type=experiment_type,
    )
    res = dict()
    for pipe in pipelines:
        res[pipe.release_version] = emg_models.AnalysisJob.objects.create(
            job_id=pipe.pk,
            study=study,
            sample=sample,
            run=run,
            run_status_id=4,
            experiment_type=experiment_type,
            pipeline=pipe,
            analysis_status=analysis_status,
            input_file_name='ABC_FASTQ',
            result_directory='test_data/version_{}/ABC_FASTQ'.format(pipe.release_version),
            submit_time='1970-01-01 00:00:00',
        )
    return res


@pytest.fixture
def var_names():
    data = (
        'collection date',
        'geographic location (latitude)',
        'geographic location (longitude)',
        'ENA checklist',
        'host taxid',
        'host scientific name'
    )
    variable_names = []
    for i, name in enumerate(data):
        variable_names.append(emg_models.VariableNames(var_id=i, var_name=name))
    emg_models.VariableNames.objects.bulk_create(variable_names)


@pytest.fixture
def analysis_metadata_variable_names():
    variable_names = (
        ("Submitted nucleotide sequences", "n/a"),
        ("Nucleotide sequences after format-specific filtering", "n/a"),
        ("Nucleotide sequences after length filtering", "n/a"),
        ("Nucleotide sequences after undetermined bases filtering", "n/a"),
        ("Total InterProScan matches", "n/a"),
        ("Predicted CDS with InterProScan match", "n/a"),
        ("Contigs with InterProScan match", "n/a"),
        ("Predicted CDS", "n/a"),
        ("Contigs with predicted CDS", "n/a"),
        ("Nucleotide sequences with predicted CDS", "n/a"),
        ("Contigs with predicted RNA", "n/a"),
        ("Nucleotide sequences with predicted rRNA", "n/a"),
        ("Predicted SSU sequences", "n/a"),
        ("Predicted LSU sequences", "n/a"),
    )
    _variable_names = list()
    for v in variable_names:
        _variable_names.append(
            emg_models.AnalysisMetadataVariableNames(
                var_name=v[0],
                description=v[1]
            )
        )
    emg_models.AnalysisMetadataVariableNames.objects.bulk_create(_variable_names)
