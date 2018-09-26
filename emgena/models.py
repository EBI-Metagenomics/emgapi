#!/usr/bin/env python
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

from django.db import models


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
        for field in ('id', 'from_email', 'message', 'subject'):
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
        db_column='WGS_ACC', max_length=30)

    class Meta:
        managed = False
        db_table = 'GCS_ASSEMBLY'
        app_label = 'emgena'
        unique_together = ('accession', 'legacy_accession',)
        ordering = ('accession',)

    def __str__(self):
        return self.accession
