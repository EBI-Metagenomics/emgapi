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
    description = mongoengine.StringField(required=True, max_length=255)

    meta = {
        'abstract': True,
    }


class GoTerm(BaseAnnotation):

    lineage = mongoengine.StringField(required=True, max_length=255)


class InterproIdentifier(BaseAnnotation):
    pass


class AnalysisJobAnnotation(mongoengine.EmbeddedDocument):

    count = mongoengine.IntField(required=True)

    meta = {
        'abstract': True,
    }


class AnalysisJobGoTermAnnotation(AnalysisJobAnnotation):

    go_term = mongoengine.ReferenceField(GoTerm)


class AnalysisJobGoSlimTermAnnotation(AnalysisJobAnnotation):

    go_term = mongoengine.ReferenceField(GoTerm)


class AnalysisJobInterproIdentifierAnnotation(AnalysisJobAnnotation):

    interpro_identifier = mongoengine.ReferenceField(InterproIdentifier)


class BaseAnalysisJob(mongoengine.Document):

    accession = mongoengine.StringField(
        primary_key=True, required=True,
        max_length=20, unique_with=('pipeline_version'))
    pipeline_version = mongoengine.StringField(
        required=True, max_length=20,
        unique_with=('accession'))
    meta = {
        'abstract': True,
    }


class AnalysisJobGoTerm(BaseAnalysisJob):

    go_terms = mongoengine.EmbeddedDocumentListField(
        AnalysisJobGoTermAnnotation, required=False)


class AnalysisJobGoSlimTerm(BaseAnalysisJob):

    go_slim = mongoengine.EmbeddedDocumentListField(
        AnalysisJobGoSlimTermAnnotation, required=False)


class AnalysisJobInterproIdentifier(BaseAnalysisJob):

    interpro_identifiers = mongoengine.EmbeddedDocumentListField(
        AnalysisJobInterproIdentifierAnnotation, required=False)
