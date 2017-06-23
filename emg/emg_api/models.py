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


# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals

from django.db import models


class AnalysisJob(models.Model):
    job_id = models.BigAutoField(db_column='JOB_ID', primary_key=True)  # Field name made lowercase.
    job_operator = models.CharField(db_column='JOB_OPERATOR', max_length=15)  # Field name made lowercase.
    pipeline = models.ForeignKey('PipelineRelease', models.DO_NOTHING, db_column='PIPELINE_ID', related_name='analysis_jobs')  # Field name made lowercase.
    submit_time = models.DateTimeField(db_column='SUBMIT_TIME')  # Field name made lowercase.
    complete_time = models.DateTimeField(db_column='COMPLETE_TIME', blank=True, null=True)  # Field name made lowercase.
    analysis_status = models.ForeignKey('AnalysisStatus', models.DO_NOTHING, db_column='ANALYSIS_STATUS_ID')  # Field name made lowercase.
    re_run_count = models.IntegerField(db_column='RE_RUN_COUNT', blank=True, null=True)  # Field name made lowercase.
    input_file_name = models.CharField(db_column='INPUT_FILE_NAME', max_length=50)  # Field name made lowercase.
    result_directory = models.CharField(db_column='RESULT_DIRECTORY', max_length=100)  # Field name made lowercase.
    external_run_ids = models.CharField(db_column='EXTERNAL_RUN_IDS', max_length=100, blank=True, null=True)  # Field name made lowercase.
    sample = models.ForeignKey('Sample', models.DO_NOTHING, db_column='SAMPLE_ID', blank=True, null=True, related_name='analysis_jobs')  # Field name made lowercase.
    is_production_run = models.TextField(db_column='IS_PRODUCTION_RUN', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    experiment_type = models.ForeignKey('ExperimentType', models.DO_NOTHING, db_column='EXPERIMENT_TYPE_ID', blank=True, null=True)  # Field name made lowercase.
    run_status_id = models.IntegerField(db_column='RUN_STATUS_ID', blank=True, null=True)  # Field name made lowercase.
    instrument_platform = models.CharField(db_column='INSTRUMENT_PLATFORM', max_length=50, blank=True, null=True)  # Field name made lowercase.
    instrument_model = models.CharField(db_column='INSTRUMENT_MODEL', max_length=50, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ANALYSIS_JOB'


class AnalysisStatus(models.Model):
    analysis_status_id = models.AutoField(db_column='ANALYSIS_STATUS_ID', primary_key=True)  # Field name made lowercase.
    analysis_status = models.CharField(db_column='ANALYSIS_STATUS', max_length=25)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ANALYSIS_STATUS'


class Biome(models.Model):
    biome_id = models.SmallIntegerField(db_column='BIOME_ID', primary_key=True)  # Field name made lowercase.
    biome_name = models.CharField(db_column='BIOME_NAME', max_length=60)  # Field name made lowercase.
    lft = models.SmallIntegerField(db_column='LFT')  # Field name made lowercase.
    rgt = models.SmallIntegerField(db_column='RGT')  # Field name made lowercase.
    depth = models.IntegerField(db_column='DEPTH')  # Field name made lowercase.
    lineage = models.CharField(db_column='LINEAGE', max_length=500)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'BIOME_HIERARCHY_TREE'


class BlacklistedStudy(models.Model):
    accession = models.CharField(db_column='EXT_STUDY_ID', primary_key=True, max_length=18)  # Field name made lowercase.
    error_type = models.ForeignKey('StudyErrorType', models.DO_NOTHING, db_column='ERROR_TYPE_ID')  # Field name made lowercase.
    analyzer = models.CharField(db_column='ANALYZER', max_length=15)  # Field name made lowercase.
    pipeline_id = models.IntegerField(db_column='PIPELINE_ID', blank=True, null=True)  # Field name made lowercase.
    date_blacklisted = models.DateField(db_column='DATE_BLACKLISTED')  # Field name made lowercase.
    comment = models.TextField(db_column='COMMENT', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'BLACKLISTED_STUDY'


class ExperimentType(models.Model):
    experiment_type_id = models.AutoField(db_column='EXPERIMENT_TYPE_ID', primary_key=True)  # Field name made lowercase.
    experiment_type = models.CharField(db_column='EXPERIMENT_TYPE', max_length=30)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'EXPERIMENT_TYPE'


class GscCvCv(models.Model):
    var_name = models.ForeignKey('VariableNames', models.DO_NOTHING, db_column='VAR_NAME', blank=True, null=True)  # Field name made lowercase.
    var_val_cv = models.CharField(db_column='VAR_VAL_CV', primary_key=True, max_length=60)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'GSC_CV_CV'
        unique_together = (('var_name', 'var_val_cv'),)


class PipelineRelease(models.Model):
    pipeline_id = models.AutoField(db_column='PIPELINE_ID', primary_key=True)  # Field name made lowercase.
    description = models.TextField(db_column='DESCRIPTION', blank=True, null=True)  # Field name made lowercase.
    changes = models.TextField(db_column='CHANGES')  # Field name made lowercase.
    release_version = models.CharField(db_column='RELEASE_VERSION', max_length=20)  # Field name made lowercase.
    release_date = models.DateField(db_column='RELEASE_DATE')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'PIPELINE_RELEASE'


class PipelineReleaseTool(models.Model):
    pipeline = models.ForeignKey(PipelineRelease, models.DO_NOTHING, db_column='PIPELINE_ID', primary_key=True)  # Field name made lowercase.
    tool = models.ForeignKey('PipelineTool', models.DO_NOTHING, db_column='TOOL_ID')  # Field name made lowercase.
    tool_group_id = models.DecimalField(db_column='TOOL_GROUP_ID', max_digits=6, decimal_places=3)  # Field name made lowercase.
    how_tool_used_desc = models.TextField(db_column='HOW_TOOL_USED_DESC')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'PIPELINE_RELEASE_TOOL'
        unique_together = (('pipeline', 'tool'), ('pipeline', 'tool_group_id'),)


class PipelineTool(models.Model):
    tool_id = models.SmallIntegerField(db_column='TOOL_ID', primary_key=True)  # Field name made lowercase.
    tool_name = models.CharField(db_column='TOOL_NAME', max_length=30)  # Field name made lowercase.
    description = models.TextField(db_column='DESCRIPTION')  # Field name made lowercase.
    web_link = models.CharField(db_column='WEB_LINK', max_length=500, blank=True, null=True)  # Field name made lowercase.
    version = models.CharField(db_column='VERSION', max_length=30)  # Field name made lowercase.
    exe_command = models.CharField(db_column='EXE_COMMAND', max_length=500)  # Field name made lowercase.
    installation_dir = models.CharField(db_column='INSTALLATION_DIR', max_length=200, blank=True, null=True)  # Field name made lowercase.
    configuration_file = models.TextField(db_column='CONFIGURATION_FILE', blank=True, null=True)  # Field name made lowercase.
    notes = models.TextField(db_column='NOTES', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'PIPELINE_TOOL'


class Publication(models.Model):
    pub_id = models.AutoField(db_column='PUB_ID', primary_key=True)  # Field name made lowercase.
    authors = models.CharField(db_column='AUTHORS', max_length=4000, blank=True, null=True)  # Field name made lowercase.
    doi = models.CharField(db_column='DOI', max_length=1500, blank=True, null=True)  # Field name made lowercase.
    isbn = models.CharField(db_column='ISBN', max_length=100, blank=True, null=True)  # Field name made lowercase.
    iso_journal = models.CharField(db_column='ISO_JOURNAL', max_length=255, blank=True, null=True)  # Field name made lowercase.
    issue = models.CharField(db_column='ISSUE', max_length=55, blank=True, null=True)  # Field name made lowercase.
    medline_journal = models.CharField(db_column='MEDLINE_JOURNAL', max_length=255, blank=True, null=True)  # Field name made lowercase.
    pub_abstract = models.TextField(db_column='PUB_ABSTRACT', blank=True, null=True)  # Field name made lowercase.
    pubmed_central_id = models.IntegerField(db_column='PUBMED_CENTRAL_ID', blank=True, null=True)  # Field name made lowercase.
    pubmed_id = models.IntegerField(db_column='PUBMED_ID', blank=True, null=True)  # Field name made lowercase.
    pub_title = models.CharField(db_column='PUB_TITLE', max_length=740)  # Field name made lowercase.
    raw_pages = models.CharField(db_column='RAW_PAGES', max_length=30, blank=True, null=True)  # Field name made lowercase.
    url = models.CharField(db_column='URL', max_length=740, blank=True, null=True)  # Field name made lowercase.
    volume = models.CharField(db_column='VOLUME', max_length=55, blank=True, null=True)  # Field name made lowercase.
    published_year = models.SmallIntegerField(db_column='PUBLISHED_YEAR', blank=True, null=True)  # Field name made lowercase.
    pub_type = models.CharField(db_column='PUB_TYPE', max_length=150, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'PUBLICATION'


class Sample(models.Model):
    sample_id = models.AutoField(db_column='SAMPLE_ID', primary_key=True)  # Field name made lowercase.
    analysis_completed = models.DateField(db_column='ANALYSIS_COMPLETED', blank=True, null=True)  # Field name made lowercase.
    collection_date = models.DateField(db_column='COLLECTION_DATE', blank=True, null=True)  # Field name made lowercase.
    geo_loc_name = models.CharField(db_column='GEO_LOC_NAME', max_length=255, blank=True, null=True)  # Field name made lowercase.
    is_public = models.IntegerField(db_column='IS_PUBLIC', blank=True, null=True)  # Field name made lowercase.
    metadata_received = models.DateTimeField(db_column='METADATA_RECEIVED', blank=True, null=True)  # Field name made lowercase.
    sample_desc = models.TextField(db_column='SAMPLE_DESC', blank=True, null=True)  # Field name made lowercase.
    sequencedata_archived = models.DateTimeField(db_column='SEQUENCEDATA_ARCHIVED', blank=True, null=True)  # Field name made lowercase.
    sequencedata_received = models.DateTimeField(db_column='SEQUENCEDATA_RECEIVED', blank=True, null=True)  # Field name made lowercase.
    environment_biome = models.CharField(db_column='ENVIRONMENT_BIOME', max_length=255, blank=True, null=True)  # Field name made lowercase.
    environment_feature = models.CharField(db_column='ENVIRONMENT_FEATURE', max_length=255, blank=True, null=True)  # Field name made lowercase.
    environment_material = models.CharField(db_column='ENVIRONMENT_MATERIAL', max_length=255, blank=True, null=True)  # Field name made lowercase.
    study = models.ForeignKey('Study', models.DO_NOTHING, db_column='STUDY_ID', blank=True, null=True, related_name='samples')  # Field name made lowercase.
    sample_name = models.CharField(db_column='SAMPLE_NAME', max_length=255, blank=True, null=True)  # Field name made lowercase.
    sample_alias = models.CharField(db_column='SAMPLE_ALIAS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    host_tax_id = models.IntegerField(db_column='HOST_TAX_ID', blank=True, null=True)  # Field name made lowercase.
    accession = models.CharField(db_column='EXT_SAMPLE_ID', max_length=15)  # Field name made lowercase.
    species = models.CharField(db_column='SPECIES', max_length=255, blank=True, null=True)  # Field name made lowercase.
    latitude = models.DecimalField(db_column='LATITUDE', max_digits=7, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    longitude = models.DecimalField(db_column='LONGITUDE', max_digits=7, decimal_places=4, blank=True, null=True)  # Field name made lowercase.
    last_update = models.DateTimeField(db_column='LAST_UPDATE')  # Field name made lowercase.
    submission_account_id = models.CharField(db_column='SUBMISSION_ACCOUNT_ID', max_length=15, blank=True, null=True)  # Field name made lowercase.
    biome = models.ForeignKey(Biome, models.DO_NOTHING, db_column='BIOME_ID', blank=True, null=True, related_name='samples')  # Field name made lowercase.

    class Meta:
        unique_together = (('sample_id', 'accession'),)
        managed = False
        db_table = 'SAMPLE'


class SampleAnn(models.Model):
    sample = models.ForeignKey(Sample, models.DO_NOTHING, db_column='SAMPLE_ID', primary_key=True)  # Field name made lowercase.
    var_val_cv = models.ForeignKey(GscCvCv, models.DO_NOTHING, db_column='VAR_VAL_CV', blank=True, null=True)  # Field name made lowercase.
    units = models.CharField(db_column='UNITS', max_length=25, blank=True, null=True)  # Field name made lowercase.
    var = models.ForeignKey('VariableNames', models.DO_NOTHING, db_column='VAR_ID')  # Field name made lowercase.
    var_val_ucv = models.CharField(db_column='VAR_VAL_UCV', max_length=4000, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'SAMPLE_ANN'
        unique_together = (('sample', 'var'), ('sample', 'var'),)


class SamplePublication(models.Model):
    sample = models.ForeignKey(Sample, models.DO_NOTHING, db_column='SAMPLE_ID', primary_key=True)  # Field name made lowercase.
    pub = models.ForeignKey(Publication, models.DO_NOTHING, db_column='PUB_ID')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'SAMPLE_PUBLICATION'
        unique_together = (('sample', 'pub'),)


class Study(models.Model):
    study_id = models.AutoField(db_column='STUDY_ID', primary_key=True)  # Field name made lowercase.
    centre_name = models.CharField(db_column='CENTRE_NAME', max_length=255, blank=True, null=True)  # Field name made lowercase.
    experimental_factor = models.CharField(db_column='EXPERIMENTAL_FACTOR', max_length=255, blank=True, null=True)  # Field name made lowercase.
    is_public = models.IntegerField(db_column='IS_PUBLIC', blank=True, null=True)  # Field name made lowercase.
    ncbi_project_id = models.IntegerField(db_column='NCBI_PROJECT_ID', blank=True, null=True)  # Field name made lowercase.
    public_release_date = models.DateField(db_column='PUBLIC_RELEASE_DATE', blank=True, null=True)  # Field name made lowercase.
    study_abstract = models.TextField(db_column='STUDY_ABSTRACT', blank=True, null=True)  # Field name made lowercase.
    accession = models.CharField(db_column='EXT_STUDY_ID', max_length=18)  # Field name made lowercase.
    study_name = models.CharField(db_column='STUDY_NAME', max_length=255, blank=True, null=True)  # Field name made lowercase.
    study_status = models.CharField(db_column='STUDY_STATUS', max_length=30, blank=True, null=True)  # Field name made lowercase.
    data_origination = models.CharField(db_column='DATA_ORIGINATION', max_length=20, blank=True, null=True)  # Field name made lowercase.
    author_email = models.CharField(db_column='AUTHOR_EMAIL', max_length=100, blank=True, null=True)  # Field name made lowercase.
    author_name = models.CharField(db_column='AUTHOR_NAME', max_length=100, blank=True, null=True)  # Field name made lowercase.
    last_update = models.DateTimeField(db_column='LAST_UPDATE')  # Field name made lowercase.
    submission_account_id = models.CharField(db_column='SUBMISSION_ACCOUNT_ID', max_length=15, blank=True, null=True)  # Field name made lowercase.
    biome = models.ForeignKey(Biome, models.DO_NOTHING, db_column='BIOME_ID', blank=True, null=True, related_name='studies')  # Field name made lowercase.
    result_directory = models.CharField(db_column='RESULT_DIRECTORY', max_length=100, blank=True, null=True)  # Field name made lowercase.
    first_created = models.DateTimeField(db_column='FIRST_CREATED')  # Field name made lowercase.
    project_id = models.CharField(db_column='PROJECT_ID', max_length=18, blank=True, null=True)  # Field name made lowercase.

    # manualy added StudyPublication
    publications = models.ManyToManyField(Publication, through='StudyPublication', related_name='studies')

    class Meta:
        # manualy added make sure both are unique
        unique_together = (('study_id', 'accession'),)
        managed = False
        db_table = 'STUDY'


class StudyErrorType(models.Model):
    error_id = models.IntegerField(db_column='ERROR_ID', primary_key=True)  # Field name made lowercase.
    error_type = models.CharField(db_column='ERROR_TYPE', max_length=50)  # Field name made lowercase.
    description = models.TextField(db_column='DESCRIPTION')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'STUDY_ERROR_TYPE'


class StudyPublication(models.Model):
    study = models.ForeignKey(Study, models.DO_NOTHING, db_column='STUDY_ID', primary_key=True)  # Field name made lowercase.
    pub = models.ForeignKey(Publication, models.DO_NOTHING, db_column='PUB_ID')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'STUDY_PUBLICATION'
        unique_together = (('study', 'pub'),)


class VariableNames(models.Model):
    var_id = models.SmallIntegerField(db_column='VAR_ID', primary_key=True)  # Field name made lowercase.
    var_name = models.CharField(db_column='VAR_NAME', unique=True, max_length=50)  # Field name made lowercase.
    definition = models.TextField(db_column='DEFINITION', blank=True, null=True)  # Field name made lowercase.
    value_syntax = models.CharField(db_column='VALUE_SYNTAX', max_length=250, blank=True, null=True)  # Field name made lowercase.
    alias = models.CharField(db_column='ALIAS', max_length=30, blank=True, null=True)  # Field name made lowercase.
    authority = models.CharField(db_column='AUTHORITY', max_length=30, blank=True, null=True)  # Field name made lowercase.
    sra_xml_attribute = models.CharField(db_column='SRA_XML_ATTRIBUTE', max_length=30, blank=True, null=True)  # Field name made lowercase.
    required_for_mimarks_complianc = models.CharField(db_column='REQUIRED_FOR_MIMARKS_COMPLIANC', max_length=1, blank=True, null=True)  # Field name made lowercase.
    required_for_mims_compliance = models.CharField(db_column='REQUIRED_FOR_MIMS_COMPLIANCE', max_length=1, blank=True, null=True)  # Field name made lowercase.
    gsc_env_packages = models.CharField(db_column='GSC_ENV_PACKAGES', max_length=250, blank=True, null=True)  # Field name made lowercase.
    comments = models.CharField(db_column='COMMENTS', max_length=250, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'VARIABLE_NAMES'
        unique_together = (('var_id', 'var_name'), ('var_id', 'var_name'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


# CREATE FULLTEXT INDEX STUDY_ABSTRACT_IDX ON STUDY (study_abstract);
# CREATE FULLTEXT INDEX STUDY_NAME_IDX ON STUDY (study_name);
# CREATE FULLTEXT INDEX PUBLICATION_TITLE_IDX ON PUBLICATION (pub_title);
# CREATE FULLTEXT INDEX PIPELINE_RELEASE_DESCRIPTION_IDX ON PIPELINE_RELEASE (description);
# CREATE FULLTEXT INDEX PIPELINE_RELEASE_CHANGES_IDX ON PIPELINE_RELEASE (changes);