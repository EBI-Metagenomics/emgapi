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

import mongoengine


class BaseAnnotation(mongoengine.DynamicDocument):

    accession = mongoengine.StringField(
        primary_key=True, required=True,
        max_length=20, unique_with=('description'))
    description = mongoengine.StringField(
        required=True, max_length=255,
        unique_with=('accession'))

    meta = {
        'abstract': True,
    }


class GoTerm(BaseAnnotation):

    lineage = mongoengine.StringField(required=True, max_length=255)


class InterproIdentifier(BaseAnnotation):
    pass


class BaseAnalysisJobAnnotation(mongoengine.EmbeddedDocument):

    count = mongoengine.IntField(required=True)

    meta = {
        'abstract': True,
    }


class AnalysisJobGoTermAnnotation(BaseAnalysisJobAnnotation):

    go_term = mongoengine.ReferenceField(GoTerm)


class AnalysisJobInterproIdentifierAnnotation(BaseAnalysisJobAnnotation):

    interpro_identifier = mongoengine.ReferenceField(InterproIdentifier)


class BaseAnalysisJob(mongoengine.Document):

    analysis_id = mongoengine.StringField(primary_key=True, required=True,
                                          max_length=50)
    accession = mongoengine.StringField(required=True, max_length=20)
    pipeline_version = mongoengine.StringField(required=True, max_length=5)
    job_id = mongoengine.IntField(required=True)

    meta = {
        'abstract': True,
        # 'indexes': [
        #     'accession',
        #     'pipeline_version',
        #     'job_id',
        # ]
    }


class AnalysisJobGoTerm(BaseAnalysisJob):

    go_terms = mongoengine.EmbeddedDocumentListField(
        AnalysisJobGoTermAnnotation, required=False)

    go_slim = mongoengine.EmbeddedDocumentListField(
        AnalysisJobGoTermAnnotation, required=False)


class AnalysisJobInterproIdentifier(BaseAnalysisJob):

    interpro_identifiers = mongoengine.EmbeddedDocumentListField(
        AnalysisJobInterproIdentifierAnnotation, required=False)
