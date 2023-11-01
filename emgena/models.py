# -*- coding: utf-8 -*-

# Copyright 2018 EMBL - European Bioinformatics Institute
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
#   * Remove `managed = False` lines if you wish to allow Django to create,
#     modify, and delete the table
# Feel free to rename the models, but don't rename db_table values
# or field names.

from __future__ import unicode_literals

from datetime import date
from django.db import models, NotSupportedError


class Status(models.IntegerChoices):
    DRAFT = 1
    PRIVATE = 2
    CANCELLED = 3
    PUBLIC = 4
    SUPPRESSED = 5
    KILLED = 6
    TEMPORARY_SUPPRESSED = 7
    TEMPORARY_KILLED = 8


class Submitter(models.Model):
    submission_account = models.ForeignKey(
        'SubmitterContact', db_column='SUBMISSION_ACCOUNT_ID',
        primary_key=True, max_length=15, on_delete=models.CASCADE)
    analysis = models.BooleanField(
        db_column='ROLE_METAGENOME_ANALYSIS', default=False)
    submitter = models.BooleanField(
        db_column='ROLE_METAGENOME_SUBMITTER', default=False)

    @property
    def email_address(self):
        return self.submission_account.email_address

    @property
    def first_name(self):
        return self.submission_account.first_name

    @property
    def surname(self):
        return self.submission_account.surname

    class Meta:
        managed = False
        db_table = 'SUBMISSION_ACCOUNT'
        app_label = 'emgena'

    def __str__(self):
        return self.submission_account


class SubmitterContact(models.Model):
    submission_account = models.CharField(
        db_column='SUBMISSION_ACCOUNT_ID', primary_key=True, max_length=15)
    first_name = models.CharField(
        db_column='FIRST_NAME', max_length=30)
    surname = models.CharField(
        db_column='SURNAME', max_length=50)
    email_address = models.CharField(
        db_column='EMAIL_ADDRESS', max_length=200)

    class Meta:
        managed = False
        db_table = 'SUBMISSION_CONTACT'
        app_label = 'emgena'
        unique_together = ('submission_account', 'email_address',)
        ordering = ('submission_account',)

    def __str__(self):
        return self.submission_account


class Notify(object):
    def __init__(self, **kwargs):
        for field in ('id', 'from_email', 'message', 'subject', 'is_consent', 'cc'):
            setattr(self, field, kwargs.get(field, None))


# helpers

class AssemblyMapping(models.Model):
    submission_account = models.CharField(
        db_column='SUBMISSION_ACCOUNT_ID', primary_key=True, max_length=15)
    accession = models.CharField(
        db_column='ASSEMBLY_ID', max_length=30)
    name = models.CharField(
        db_column='NAME', max_length=30)
    legacy_accession = models.CharField(
        db_column='GC_ID', max_length=30)
    legacy_version = models.CharField(
        db_column='GC_VERSION', max_length=30)
    wgs_accession = models.CharField(
        db_column='WGS_ACC', max_length=30, null=True)
    sample_id = models.CharField(
        db_column='SAMPLE_ID', max_length=30
    )
    biosample_id = models.CharField(
        db_column='BIOSAMPLE_ID', max_length=30
    )
    submission_id = models.CharField(
        db_column='SUBMISSION_ID', max_length=30
    )
    status = models.CharField(
        db_column='STATUS_ID', max_length=5
    )
    assembly_type = models.CharField(
        db_column='ASSEMBLY_TYPE', max_length=30
    )
    project_accession = models.CharField(
        db_column='PROJECT_ACC', max_length=30
    )
    coverage = models.CharField(
        db_column='COVERAGE', max_length=30
    )
    min_gap_length = models.CharField(
        db_column='MIN_GAP_LENGTH', max_length=30, null=True
    )
    contig_accession_range = models.CharField(
        db_column='CONTIG_ACC_RANGE', max_length=100
    )


    class Meta:
        managed = False
        db_table = 'GCS_ASSEMBLY'
        app_label = 'emgena'
        unique_together = ('accession', 'legacy_accession',)
        ordering = ('accession',)

    def __str__(self):
        return self.accession


class StudyAbstract(models.Model):
    study_id = models.CharField(db_column='STUDY_ID', primary_key=True, max_length=15)
    project_id = models.CharField(db_column='PROJECT_ID', max_length=15)
    study_status = models.CharField(db_column='STUDY_STATUS', max_length=50, choices=Status.choices)
    center_name = models.TextField(db_column='CENTER_NAME', max_length=500)
    hold_date = models.DateTimeField(db_column='HOLD_DATE', null=True)
    first_created = models.DateTimeField(db_column='FIRST_CREATED')
    last_updated = models.DateTimeField(db_column='LAST_UPDATED')
    study_title = models.TextField(db_column='STUDY_TITLE', max_length=4000)
    study_description = models.TextField(db_column='STUDY_DESCRIPTION')
    submission_account_id = models.CharField(db_column='SUBMISSION_ACCOUNT_ID', max_length=15)
    pubmed_id = models.TextField(db_column='PUBMED_ID', max_length=4000)

    @property
    def get_study_id(self):
        return self.study_id

    def __str__(self):
        return '%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s' % (
            self.study_id, self.project_id, self.study_status, self.center_name, self.hold_date, self.first_created,
            self.last_updated, self.study_title, self.study_description, self.submission_account_id, self.pubmed_id)

    class Meta:
        managed = False
        app_label = 'emgena'
        abstract = True


class Study(models.Model):
    study_id = models.CharField(db_column='STUDY_ID', primary_key=True, max_length=15)
    study_status = models.CharField(db_column='STATUS_ID', max_length=50, choices=Status.choices)
    hold_date = models.DateTimeField(db_column='HOLD_DATE')

    class Meta:
        managed = False
        app_label = 'emgena'
        db_table = 'STUDY'


class RunStudy(StudyAbstract):
    class Meta(StudyAbstract.Meta):
        # ERA needs to be appended as the default connection tries to use
        # the PUBLIC SYNONYM (according to ENA) and it's not working ATM
        # we were advised to prefix the views and this is the simplest way.
        # The short-term plan is to remove the dependency of ENA databases 
        db_table = 'ERA\".\"V_MGP_RUN_STUDY'


class AssemblyStudy(StudyAbstract):
    class Meta(StudyAbstract.Meta):
        # ERA needs to be appended as the default connection tries to use
        # the PUBLIC SYNONYM (according to ENA) and it's not working ATM
        # we were advised to prefix the views and this is the simplest way.
        # The short-term plan is to remove the dependency of ENA databases 
        db_table = 'ERA\".\"V_MGP_ASSEMBLY_STUDY'


class Project(models.Model):
    project_id = models.CharField(db_column='PROJECT_ID', primary_key=True, max_length=15)
    center_name = models.TextField(db_column='CENTER_NAME', max_length=500)

    class Meta:
        managed = False
        app_label = 'emgena'
        db_table = 'PROJECT'


class Sample(models.Model):
    sample_id = models.CharField(db_column='SAMPLE_ID', primary_key=True, max_length=15)
    submission_id = models.CharField(db_column='SUBMISSION_ID', max_length=15)
    biosample_id = models.CharField(db_column='BIOSAMPLE_ID', max_length=15)
    submission_account_id = models.CharField(db_column='SUBMISSION_ACCOUNT_ID', max_length=15)
    first_created = models.DateField(db_column='FIRST_CREATED')
    last_updated = models.DateField(db_column='LAST_UPDATED')
    first_public = models.DateField(db_column='FIRST_PUBLIC')
    status_id = models.IntegerField(db_column='STATUS_ID', choices=Status.choices)
    tax_id = models.IntegerField(db_column='TAX_ID')
    scientific_name = models.CharField(db_column='SCIENTIFIC_NAME', max_length=100)
    title = models.CharField(db_column='SAMPLE_TITLE', max_length=200)
    alias = models.CharField(db_column='SAMPLE_ALIAS', max_length=200)
    checklist = models.CharField(db_column='CHECKLIST_ID', max_length=200, null=True)

    @property
    def is_public(self):
        return date.today() >= self.first_public

    class Meta:
        managed = False
        app_label = 'emgena'
        db_table = 'SAMPLE'


class Run(models.Model):
    run_id = models.CharField(db_column='RUN_ID', primary_key=True, max_length=15)
    submission_id = models.CharField(db_column='SUBMISSION_ID', max_length=15)
    experiment_id = models.CharField(db_column='EXPERIMENT_ID', max_length=15)
    alias = models.CharField(db_column='RUN_ALIAS', max_length=100)
    status_id = models.IntegerField(db_column='STATUS_ID', choices=Status.choices)
    first_created = models.DateField(db_column='FIRST_CREATED')
    last_updated = models.DateField(db_column='LAST_UPDATED')
    submission_account_id = models.CharField(db_column='SUBMISSION_ACCOUNT_ID', max_length=15)

    class Meta:
        managed = False
        app_label = 'emgena'
        db_table = 'RUN'


class Analysis(models.Model):
    analysis_id = models.CharField(db_column='ANALYSIS_ID', primary_key=True, max_length=15)
    title = models.CharField(db_column='ANALYSIS_TITLE', max_length=100)
    type = models.CharField(db_column='ANALYSIS_TYPE', max_length=100)
    submission_id = models.CharField(db_column='SUBMISSION_ID', max_length=15)
    status_id = models.IntegerField(db_column='STATUS_ID')
    first_created = models.DateField(db_column='FIRST_CREATED')
    last_updated = models.DateField(db_column='LAST_UPDATED')
    primary_study_accession = models.CharField(db_column='BIOPROJECT_ID', max_length=15)
    secondary_study_accession = models.CharField(db_column='STUDY_ID', max_length=15)
    unique_alias = models.CharField(db_column='UNIQUE_ALIAS', max_length=100)
    submission_account_id = models.CharField(db_column='SUBMISSION_ACCOUNT_ID', max_length=15)

    class Meta:
        managed = False
        app_label = 'emgena'
        db_table = 'ANALYSIS'


class Assembly(models.Model):
    assembly_id = models.CharField(db_column='ASSEMBLY_ID', primary_key=True, max_length=15)
    sample_id = models.CharField(db_column='SAMPLE_ID', max_length=15)
    biosample_id = models.CharField(db_column='BIOSAMPLE_ID', max_length=15)
    submission_account_id = models.CharField(db_column='SUBMISSION_ACCOUNT_ID', max_length=15)
    submission_id = models.CharField(db_column='SUBMISSION_ID', max_length=15)
    status_id = models.IntegerField(db_column='STATUS_ID', choices=Status.choices)
    gc_id = models.CharField(db_column='GC_ID', max_length=15)
    assembly_type = models.IntegerField(db_column='ASSEMBLY_TYPE')
    primary_study_accession = models.CharField(db_column='PROJECT_ACC', max_length=50)

    name = models.CharField(db_column='NAME', max_length=50)
    wgs_accession = models.CharField(db_column='WGS_ACC', max_length=50)
    coverage = models.IntegerField(db_column='COVERAGE')
    min_gap_length = models.IntegerField(db_column='MIN_GAP_LENGTH', null=True, blank=True)
    contig_accession_range = models.CharField(db_column='CONTIG_ACC_RANGE', max_length=50)

    class Meta:
        managed = False
        app_label = 'emgena'
        db_table = 'gcs_assembly'
