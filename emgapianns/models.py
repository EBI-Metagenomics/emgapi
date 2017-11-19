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


# Annotations model

class BaseAnnotation(mongoengine.DynamicDocument):

    accession = mongoengine.StringField(primary_key=True, required=True,
                                        max_length=20)
    description = mongoengine.StringField(required=True, max_length=255)

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

    go_term = mongoengine.ReferenceField(GoTerm, required=True)

    @property
    def accession(self):
        return self.go_term.accession

    @property
    def description(self):
        return self.go_term.description

    @property
    def lineage(self):
        return self.go_term.lineage


class AnalysisJobInterproIdentifierAnnotation(BaseAnalysisJobAnnotation):

    interpro_identifier = mongoengine.ReferenceField(InterproIdentifier,
                                                     required=True)

    @property
    def accession(self):
        return self.interpro_identifier.accession

    @property
    def description(self):
        return self.interpro_identifier.description

    @property
    def lineage(self):
        return self.interpro_identifier.lineage


class BaseAnalysisJob(mongoengine.Document):

    analysis_id = mongoengine.StringField(primary_key=True, required=True,
                                          max_length=50)
    accession = mongoengine.StringField(required=True, max_length=20)
    pipeline_version = mongoengine.StringField(required=True, max_length=5)
    job_id = mongoengine.IntField(required=True)

    meta = {
        'abstract': True,
    }


class AnalysisJobGoTerm(BaseAnalysisJob):

    go_terms = mongoengine.EmbeddedDocumentListField(
        AnalysisJobGoTermAnnotation, required=False)

    go_slim = mongoengine.EmbeddedDocumentListField(
        AnalysisJobGoTermAnnotation, required=False)


class AnalysisJobInterproIdentifier(BaseAnalysisJob):

    interpro_identifiers = mongoengine.EmbeddedDocumentListField(
        AnalysisJobInterproIdentifierAnnotation, required=False)


# Taxonomic model

class Organism(mongoengine.Document):

    id = mongoengine.StringField(primary_key=True)
    lineage = mongoengine.StringField(required=True)
    ancestors = mongoengine.ListField(mongoengine.StringField(), default=list)
    hierarchy = mongoengine.DictField()
    domain = mongoengine.StringField()
    name = mongoengine.StringField()
    parent = mongoengine.StringField()
    rank = mongoengine.StringField()
    pipeline_version = mongoengine.StringField(required=True)

    meta = {
        'ordering': ['lineage']
    }


class AnalysisJobOrganism(mongoengine.EmbeddedDocument):

    count = mongoengine.IntField(required=True)
    organism = mongoengine.ReferenceField(Organism)

    @property
    def lineage(self):
        return self.organism.lineage

    @property
    def ancestors(self):
        return self.organism.ancestors

    @property
    def hierarchy(self):
        return self.organism.hierarchy

    @property
    def domain(self):
        return self.organism.domain

    @property
    def name(self):
        return self.organism.name

    @property
    def parent(self):
        return self.organism.parent

    @property
    def rank(self):
        return self.organism.rank

    @property
    def pipeline_version(self):
        return self.organism.pipeline_version


class AnalysisJobTaxonomy(mongoengine.Document):

    analysis_id = mongoengine.StringField(primary_key=True)
    accession = mongoengine.StringField(required=True)
    pipeline_version = mongoengine.StringField(required=True)
    job_id = mongoengine.IntField(required=True)

    taxonomy = mongoengine.EmbeddedDocumentListField(
        AnalysisJobOrganism, required=False)
    taxonomy_lsu = mongoengine.EmbeddedDocumentListField(
        AnalysisJobOrganism, required=False)
    taxonomy_ssu = mongoengine.EmbeddedDocumentListField(
            AnalysisJobOrganism, required=False)
