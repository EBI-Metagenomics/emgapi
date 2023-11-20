#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019-2023 EMBL - European Bioinformatics Institute
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
import uuid

from django.conf import settings

from model_bakery import baker

from emgapi import models as emg_models
from emgena import models as ena_models


__all__ = [
    'apiclient', 'api_version', 'biome', 'biome_human', 'super_study', 'studies',
    'samples', 'study', 'study_private', 'sample', 'sample_private',
    'analysis_status', 'pipeline', 'pipelines', 'experiment_type',
    'experiment_type_assembly', 'runs', 'run', 'run_v5', 'runjob_pipeline_v1',
    'run_emptyresults', 'run_with_sample', 'analysis_results', 'run_multiple_analysis',
    'var_names', 'analysis_metadata_variable_names', 'genome_catalogue', 'genome',
    'assemblies', 'legacy_mapping', 'ena_run_study', 'ena_public_studies',
    'ena_private_studies', 'ena_suppressed_studies', 'ena_public_runs', 'ena_private_runs',
    'ena_suppressed_runs', 'ena_public_samples', 'ena_private_samples', 'ena_suppressed_samples',
    'ena_public_assemblies', 'ena_private_assemblies', 'ena_suppressed_assemblies',
    'ena_suppression_propagation_samples', 'ena_suppression_propagation_assemblies',
    'assembly_extra_annotation', 'ena_suppression_propagation_studies', 'ena_suppression_propagation_runs',
    'suppressed_analysis_jobs', 'analysis_existed_in_me',
]


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
def genome_catalogue(biome_human):
    return emg_models.GenomeCatalogue.objects.create(
        biome=biome_human,
        name='Mandalorian Genomes v1.0',
        catalogue_id='mandalor-1-0',
        version='1.0'
    )


@pytest.fixture
def genome(biome_human, genome_catalogue):
    return emg_models.Genome.objects.create(
        accession='MGYG000000001',
        biome=biome_human,
        catalogue=genome_catalogue,
        length=1,
        num_contigs=1,
        n_50=1,
        gc_content=1.0,
        type=emg_models.Genome.MAG,
        completeness=1.0,
        contamination=1.0,
        rna_5s=1.0,
        rna_16s=1.0,
        rna_23s=1.0,
        trnas=1.0,
        nc_rnas=1,
        num_proteins=1,
        eggnog_coverage=1.0,
        ipr_coverage=1.0,
        taxon_lineage='d__Test;',
    )


@pytest.fixture
def super_study(study, study_private, biome):
    ss = emg_models.SuperStudy.objects.create(
        super_study_id=1,
        title='Human Microbiome',
        description='Just a test description',
        url_slug='human-microbiome',
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
    for pk in range(49, 0, -1):
        studies.append(
            emg_models.Study(
                biome=biome,
                study_id=pk,
                secondary_accession='SRP0{:0>3}'.format(pk),
                centre_name='Centre Name',
                is_private=False,
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
                is_private=False,
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
        is_private=False,
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
        is_private=True,
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
        is_private=False,
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
        is_private=True,
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
    experiment_type, _ = emg_models.ExperimentType.objects.get_or_create(
        experiment_type='metagenomic',
        defaults={'experiment_type_id': 2}
    )
    return experiment_type


@pytest.fixture
def experiment_type_assembly():
    experiment_type, _ = emg_models.ExperimentType.objects.get_or_create(
        experiment_type='assembly',
        defaults={'experiment_type_id': 4}
    )
    return experiment_type


@pytest.fixture
def runs(study, samples, analysis_status, pipeline,
         experiment_type):
    jobs = []
    for s in samples:
        pk = s.sample_id
        run, created = emg_models.Run.objects.get_or_create(
            sample=s,
            study=study,
            accession='ABC_{:0>3}'.format(pk),
            secondary_accession='DEF_{:0>3}'.format(pk),
            is_private=False,
            experiment_type=experiment_type,
        )
        _aj = emg_models.AnalysisJob(
            sample=s,
            study=study,
            run=run,
            is_private=False,
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
def run(study, sample, analysis_status, pipeline, experiment_type):
    run, _ = emg_models.Run.objects.get_or_create(
        run_id=1234,
        accession='ABC01234',
        sample=sample,
        study=study,
        is_private=False,
        experiment_type=experiment_type
    )
    emg_models.AnalysisJob.objects.create(
        job_id=1234,
        sample=sample,
        study=study,
        run=run,
        is_private=False,
        experiment_type=experiment_type,
        pipeline=pipeline,
        analysis_status=analysis_status,
        input_file_name='ABC_FASTQ',
        result_directory='test_data/version_1.0/ABC_FASTQ',
        submit_time='1970-01-01 00:00:00'
    )
    return run


@pytest.fixture
def run_v5(study, sample, analysis_status, pipelines, experiment_type):
    p5 = pipelines.filter(release_version='5.0').first()
    run, _ = emg_models.Run.objects.get_or_create(
        run_id=5555,
        accession='ABC01234',
        sample=sample,
        study=study,
        is_private=False,
        experiment_type=experiment_type
    )
    emg_models.AnalysisJob.objects.create(
        job_id=1234,
        sample=sample,
        study=study,
        run=run,
        is_private=False,
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
        is_private=False,
        experiment_type=experiment_type,
        pipeline=pipelines.filter(release_version='1.0').first(),
        analysis_status=analysis_status,
        input_file_name='ABC_FASTQ',
        result_directory='test_data/version_1.0/ABC_FASTQ',
        submit_time='1970-01-01 00:00:00'
    )


@pytest.fixture
def run_multiple_analysis(study, sample, analysis_status,
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
        is_private=False,
        experiment_type=experiment_type
    )
    _anl1 = emg_models.AnalysisJob.objects.create(
        job_id=1234,
        sample=sample,
        study=study,
        run=run,
        is_private=False,
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
        is_private=False,
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
        is_private=False,
        experiment_type=experiment_type,
        pipeline=pipeline5,
        analysis_status=analysis_status,
        input_file_name='ABC_FASTQ',
        result_directory='test_data/version_5.0/ABC_FASTQ',
        submit_time='2020-01-01 00:00:00',
    )
    return (_anl1, _anl4, _anl5)


@pytest.fixture
def run_emptyresults(study, sample, analysis_status, pipeline,
                     experiment_type):
    run = emg_models.Run.objects.create(
        run_id=1234,
        accession='ABC01234',
        sample=sample,
        study=study,
        is_private=False,
        experiment_type=experiment_type
    )
    return emg_models.AnalysisJob.objects.create(
        job_id=1234,
        sample=sample,
        study=study,
        run=run,
        is_private=False,
        experiment_type=experiment_type,
        pipeline=pipeline,
        analysis_status=analysis_status,
        input_file_name='EMPTY_ABC_FASTQ',
        result_directory='test_data/version_1.0/EMPTY_ABC_FASTQ',
        submit_time='1970-01-01 00:00:00',
    )


@pytest.fixture
def run_with_sample(study, sample, analysis_status, pipeline,
                    experiment_type):
    run = emg_models.Run.objects.create(
        run_id=1234,
        accession='ABC01234',
        is_private=False,
        sample=sample,
        study=study,
        experiment_type=experiment_type,
    )
    return emg_models.AnalysisJob.objects.create(
        job_id=1234,
        sample=sample,
        study=study,
        run=run,
        is_private=False,
        experiment_type=experiment_type,
        pipeline=pipeline,
        analysis_status=analysis_status,
        input_file_name='ABC_FASTQ',
        result_directory='test_data/version_1.0/ABC_FASTQ',
        submit_time='1970-01-01 00:00:00'
    )


@pytest.fixture
def analysis_results(study, sample, analysis_status,
                     experiment_type, pipelines):
    run = emg_models.Run.objects.create(
        run_id=1234,
        accession='ABC01234',
        is_private=False,
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
            is_private=False,
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


@pytest.fixture
def assemblies(study, runs, samples, experiment_type_assembly):
    assemblies = baker.make(emg_models.Assembly,
        study=study,
        experiment_type=experiment_type_assembly,
        _quantity=10)

    # one with a fixed ERZ9999 to be used with the legacy mapping
    assemblies.append(baker.make(emg_models.Assembly,
        accession="ERZ9999",
        study=study,
        experiment_type=experiment_type_assembly,
        _quantity=1))

    return assemblies


@pytest.fixture
def assembly_extra_annotation(assemblies):
    assembly = emg_models.Assembly.objects.get(accession="ERZ9999")

    description_label, created = emg_models.DownloadDescriptionLabel \
        .objects \
        .get_or_create(description_label='SanntiS annotation', defaults={
            "description": "SMBGC Annotation using Neural Networks Trained on Interpro Signatures"
        })

    fmt = emg_models.FileFormat \
        .objects \
        .filter(format_extension='gff', compression=False) \
        .first()

    group = emg_models.DownloadGroupType.objects.get(
        group_type='Functional analysis'
    )

    annotation = emg_models.AssemblyExtraAnnotation.objects.create(
        assembly=assembly,
        alias='extra.gff',
        description=description_label,
        file_format=fmt,
        group_type=group,
        realname='extra.gff',
    )

    return annotation


@pytest.fixture
def legacy_mapping(assemblies):
    fake_accession = "ERZ1111"
    return baker.make(emg_models.LegacyAssembly,
        legacy_accession=fake_accession,
        new_accession="ERZ999")


@pytest.fixture
def ena_run_study():
    study = ena_models.RunStudy()
    study.study_id = "ERP117125"
    study.project_id = "PRJNA278393"
    study.study_status = "public"
    study.center_name = "UNIVERSITY OF CAMBRIDGE"
    study.hold_date = None
    study.first_created = "2019-09-04 11:23:26"
    study.last_updated = "2019-09-04 11:23:26"
    study.study_title = "Dysbiosis associated with acute helminth infections in herbivorous youngstock - observations and implications"
    study.study_description = (
        "This study investigates, for the first time, the associations between acute infections by GI "
        "helminths and the faecal microbial and metabolic profiles of a cohort of equine youngstock, prior to and following "
        "treatment with parasiticides (ivermectin)."
    )
    study.submission_account_id = "Webin-99999"
    study.pubmed_id = ""
    return study


def make_suppresible_studies(quantity, emg_props=None, ena_props=None):
    emg_props = emg_props or {}
    ena_props = ena_props or {}
    studies = baker.make(emg_models.Study, _quantity=quantity, **emg_props)
    ena_studies = []
    for emg_study in studies:
        ena_studies.append(
            ena_models.Study(study_id=emg_study.secondary_accession, **ena_props)
        )
    return ena_studies


@pytest.fixture
def ena_public_studies():
    return make_suppresible_studies(
        10, ena_props={"study_status": ena_models.Status.PUBLIC}
    )


@pytest.fixture
def ena_private_studies():
    return make_suppresible_studies(
        6, ena_props={"study_status": ena_models.Status.PRIVATE}
    )


@pytest.fixture
def ena_suppressed_studies():
    """Returns:
    6 Studies that where SUPPRESSED
    5 Studies that were KILLED
    3 Studies that were CANCELLED
    The EMG studies are also suppressed.
    """
    studies = []
    emg_props = {"is_suppressed": True}
    studies.extend(
        make_suppresible_studies(
            6,
            emg_props=emg_props,
            ena_props={"study_status": ena_models.Status.SUPPRESSED},
        )
    )
    studies.extend(
        make_suppresible_studies(
            5, emg_props=emg_props, ena_props={"study_status": ena_models.Status.KILLED}
        )
    )
    studies.extend(
        make_suppresible_studies(
            3,
            emg_props=emg_props,
            ena_props={"study_status": ena_models.Status.CANCELLED},
        )
    )
    return studies

@pytest.fixture
def ena_suppression_propagation_studies(experiment_type_assembly):
    """Returns:
    2 Studies that are suppressed in ENA but not in EMG, with unsuppressed sample/assembly/run
    2 Studies that are unsuprressed in ENA and in EMG, with unsuppressed sample/assembly/run
    One sample in the ENA-suppressed studies is ALSO in an unsuppressed study.
    """
    ena_studies_to_be_suppressed = make_suppresible_studies(
        2,
        emg_props={},
        ena_props={"study_status": ena_models.Status.SUPPRESSED}
    )
    ena_studies_to_remain = make_suppresible_studies(
        2,
        emg_props={},
        ena_props={}
    )
    for study in emg_models.Study.objects.all():
        samples = baker.make(
            emg_models.Sample,
            _quantity=2,
            studies=[study]
        )
        for sample in samples:
            runs = baker.make(
                emg_models.Run,
                _quantity=2,
                study=study,
                sample=sample
            )
            for run in runs:
                assemblies = baker.make(
                    emg_models.Assembly,
                    _quantity=2,
                    runs=[run],
                    samples=[run.sample],
                    study=study,
                    experiment_type=experiment_type_assembly
                )
                for assembly in assemblies:
                    baker.make(
                        emg_models.AnalysisJob,
                        _quantity=2,
                        assembly=assembly,
                        sample=assembly.samples.first(),
                        study=study,
                    )
    emg_study_to_suppress = emg_models.Study.objects.get(secondary_accession=ena_studies_to_be_suppressed[0].study_id)
    # Share one sample across all studies
    sample = emg_study_to_suppress.samples.first()
    for study in emg_models.Study.objects.all():
        if not study.samples.filter(sample_id=sample.sample_id).exists():
            emg_models.StudySample.objects.create(study=study, sample=sample)

    return ena_studies_to_be_suppressed + ena_studies_to_remain


def make_suppresible_runs(quantity, emg_props=None, ena_props=None):
    emg_props = emg_props or {}
    ena_props = ena_props or {}
    runs = baker.make(emg_models.Run, _quantity=quantity, **emg_props)
    for run in runs:
        run.accession = str(uuid.uuid4())
        run.save()
    ena_runs = []
    for emg_run in runs:
        ena_runs.append(
            ena_models.Run(run_id=emg_run.accession, **ena_props)
        )
    return ena_runs

@pytest.fixture
def ena_public_runs():
    return make_suppresible_runs(
        10, ena_props={"status_id": ena_models.Status.PUBLIC}
    )


@pytest.fixture
def ena_private_runs():
    return make_suppresible_runs(
        6, ena_props={"status_id": ena_models.Status.PRIVATE}
    )

@pytest.fixture
def ena_suppressed_runs():
    """Returns:
    6 Studies that where SUPPRESSED
    5 Studies that were KILLED
    3 Studies that were CANCELLED
    The EMG studies are also suppressed.
    """
    runs = []
    emg_props = {"is_suppressed": True}
    runs.extend(
        make_suppresible_runs(
            6,
            emg_props=emg_props,
            ena_props={"status_id": ena_models.Status.SUPPRESSED},
        )
    )
    runs.extend(
        make_suppresible_runs(
            5, emg_props=emg_props, ena_props={"status_id": ena_models.Status.KILLED}
        )
    )
    runs.extend(
        make_suppresible_runs(
            3,
            emg_props=emg_props,
            ena_props={"status_id": ena_models.Status.CANCELLED},
        )
    )
    return runs


@pytest.fixture
def ena_suppression_propagation_runs(experiment_type_assembly, study):
    runs = make_suppresible_runs(
        2,
        emg_props={},
        ena_props={"status_id": ena_models.Status.SUPPRESSED},
    )
    runs.extend(
        make_suppresible_runs(
            2,
            emg_props={},
            ena_props={"status_id": ena_models.Status.PUBLIC}
        )
    )

    for run in emg_models.Run.objects.all():
        sample = baker.make(
            emg_models.Sample,
            _quantity=1,
            studies=[study]
        )[0]
        run.sample = sample
        run.save()
        assemblies = baker.make(
            emg_models.Assembly,
            _quantity=2,
            runs=[run],
            study=study,
            samples=[run.sample],
            experiment_type=experiment_type_assembly
        )
        for assembly in assemblies:
            baker.make(
                emg_models.AnalysisJob,
                _quantity=2,
                assembly=assembly,
                sample=assembly.samples.first(),
                study=study,
            )
    return runs


def make_suppresible_samples(quantity, emg_props=None, ena_props=None):
    emg_props = emg_props or {}
    ena_props = ena_props or {}
    samples = baker.make(emg_models.Sample, _quantity=quantity, **emg_props)
    for sample in samples:
        sample.accession = str(uuid.uuid4())[:5]
        sample.save()
    ena_samples = []
    for emg_sample in samples:
        ena_samples.append(
            ena_models.Sample(sample_id=emg_sample.accession, **ena_props)
        )
    return ena_samples

@pytest.fixture
def ena_public_samples():
    return make_suppresible_samples(
        10, ena_props={"status_id": ena_models.Status.PUBLIC}
    )


@pytest.fixture
def ena_private_samples():
    return make_suppresible_samples(
        6, ena_props={"status_id": ena_models.Status.PRIVATE}
    )

@pytest.fixture
def ena_suppressed_samples():
    """Returns:
    6 Studies that where SUPPRESSED
    5 Studies that were KILLED
    3 Studies that were CANCELLED
    The EMG studies are also suppressed.
    """
    samples = []
    emg_props = {"is_suppressed": True}
    samples.extend(
        make_suppresible_samples(
            2,
            emg_props=emg_props,
            ena_props={"status_id": ena_models.Status.SUPPRESSED},
        )
    )
    samples.extend(
        make_suppresible_samples(
            3, emg_props=emg_props, ena_props={"status_id": ena_models.Status.KILLED}
        )
    )
    samples.extend(
        make_suppresible_samples(
            7,
            emg_props=emg_props,
            ena_props={"status_id": ena_models.Status.CANCELLED},
        )
    )
    return samples


@pytest.fixture
def ena_suppression_propagation_samples(experiment_type_assembly, study):
    samples =  make_suppresible_samples(
        2,
        emg_props={},
        ena_props={"status_id": ena_models.Status.SUPPRESSED},
    )
    samples.extend(
        make_suppresible_samples(
            2,
            emg_props={},
            ena_props={"status_id": ena_models.Status.PUBLIC},
        )
    )

    for sample in emg_models.Sample.objects.all():
        runs = baker.make(
            emg_models.Run,
            _quantity=2,
            study=study,
            sample=sample
        )
        for run in runs:
            assemblies = baker.make(
                emg_models.Assembly,
                _quantity=2,
                runs=[run],
                samples=[run.sample],
                study=study,
                experiment_type=experiment_type_assembly
            )
            for assembly in assemblies:
                baker.make(
                    emg_models.AnalysisJob,
                    _quantity=2,
                    assembly=assembly,
                    sample=assembly.samples.first(),
                    study=study,
                )

    return samples


def make_suppresible_assemblies(quantity, emg_props=None, ena_props=None):
    emg_props = emg_props or {}
    ena_props = ena_props or {}
    assemblies = baker.make(emg_models.Assembly, _quantity=quantity, **emg_props)
    for assembly in assemblies:
        assembly.legacy_accession = str(uuid.uuid4())[:5]
        assembly.study = baker.make(emg_models.Study)
        assembly.save()
    ena_assemblies = []
    for emg_assembly in assemblies:
        ena_assemblies.append(
            ena_models.Assembly(gc_id=emg_assembly.legacy_accession, **ena_props)
        )
    return ena_assemblies

@pytest.fixture
def ena_public_assemblies():
    return make_suppresible_assemblies(
        54, ena_props={"status_id": ena_models.Status.PUBLIC}
    )


@pytest.fixture
def ena_private_assemblies():
    return make_suppresible_assemblies(
        6, ena_props={"status_id": ena_models.Status.PRIVATE}
    )

@pytest.fixture
def ena_suppressed_assemblies():
    """Returns:
    6 Studies that where SUPPRESSED
    5 Studies that were KILLED
    3 Studies that were CANCELLED
    The EMG studies are also suppressed.
    """
    assemblies = []
    emg_props = {"is_suppressed": True}
    assemblies.extend(
        make_suppresible_assemblies(
            32,
            emg_props=emg_props,
            ena_props={"status_id": ena_models.Status.SUPPRESSED},
        )
    )
    assemblies.extend(
        make_suppresible_assemblies(
            12, emg_props=emg_props, ena_props={"status_id": ena_models.Status.KILLED}
        )
    )
    assemblies.extend(
        make_suppresible_assemblies(
            9,
            emg_props=emg_props,
            ena_props={"status_id": ena_models.Status.CANCELLED},
        )
    )
    return assemblies


@pytest.fixture
def ena_suppression_propagation_assemblies(experiment_type_assembly, study):
    assemblies = []
    emg_props = {}
    assemblies.extend(
        make_suppresible_assemblies(
            32,
            emg_props=emg_props,
            ena_props={"status_id": ena_models.Status.SUPPRESSED},
        )
    )
    assemblies.extend(
        make_suppresible_assemblies(
            32,
            emg_props=emg_props,
            ena_props={"status_id": ena_models.Status.PUBLIC},
        )
    )
    for assembly in emg_models.Assembly.objects.all():
        baker.make(
            emg_models.AnalysisJob,
            _quantity=2,
            assembly=assembly,
            sample=assembly.samples.first(),
            study=study,
        )
    return assemblies


def make_suppressed_analysis_jobs(quantity, emg_props=None):
    emg_props = emg_props or {}
    analyses = baker.make(emg_models.AnalysisJob, _quantity=quantity, **emg_props)
    return analyses


@pytest.fixture
def suppressed_analysis_jobs(ena_suppressed_runs):
    suppressed_analysisjobs = make_suppressed_analysis_jobs(quantity=5,
                                                            emg_props={"is_suppressed": True,
                                                                       "suppressed_at": '1980-01-01 00:00:00',
                                                                       'last_populated_me': '1970-01-01 00:00:00'})
    return suppressed_analysisjobs

@pytest.fixture
def analysis_existed_in_me():
    emg_props = {
        "job_id": 147343,
        "last_populated_me": '1970-01-01 00:00:00',
        "last_updated_me": '1980-01-01 00:00:00',
        "is_suppressed": False,
        "is_private": False
    }
    return baker.make(emg_models.AnalysisJob, **emg_props)
