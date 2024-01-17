#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 EMBL - European Bioinformatics Institute
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
from django.conf import settings
# mongoengine = settings.MONGO_ENGINE

# Annotations model

class BaseAnnotation(mongoengine.DynamicDocument):
    mongoengine.connect(**settings.MONGO_CONF)
    accession = mongoengine.StringField(primary_key=True, required=True)
    description = mongoengine.StringField(required=True)

    meta = {
        'abstract': True,
    }


class GoTerm(BaseAnnotation):

    lineage = mongoengine.StringField(required=True)


class InterproIdentifier(BaseAnnotation):
    pass


class KeggModule(BaseAnnotation):
    """KEGG MODULE.
    KEGG MODULE is a collection of manually defined functional units, called KEGG modules and identified
    by the M numbers, used for annotation and biological interpretation of sequenced genomes.
    There are three types of KEGG modules:

    pathway modules – representing tight functional units in KEGG metabolic pathway maps,
                      such as M00002 (Glycolysis, core module involving three-carbon compounds)
    structural complexes – often forming molecular machineries, such as M00144 (NADH:quinone oxidoreductase,
                           prokaryotes)
    functional sets – other types of functional units, especially those that can be used to infer
                      phenotypes, such as M00363 (EHEC pathogenicity signature, Shiga toxin)

    For more information: https://www.genome.jp/kegg/module.html
    """
    name = mongoengine.StringField(required=True)


class PfamEntry(BaseAnnotation):
    """PfamEntry entry
    For more information: https://pfam.xfam.org/
    """
    pass


class COG(BaseAnnotation):
    """COG entry
    """
    meta = {
        'collection': 'cog'
    }


class KeggOrtholog(BaseAnnotation):
    """KEGG Ortholog (KO)
    """
    pass


class AntiSmashGeneCluster(BaseAnnotation):
    """antiSMASH gene cluster
    antiSMASH uses some abbreviations internally to refer to the different
    types of secondary metabolite clusters, a short explanation of the different
    types can be found https://docs.antismash.secondarymetabolites.org/glossary/
    """
    meta = {
        'collection': 'antismash_gene_cluster'
    }


class GenomeProperty(BaseAnnotation):
    """Genome property
    """
    pass


class BaseAnalysisJobAnnotation(mongoengine.EmbeddedDocument):

    count = mongoengine.IntField(required=True)

    meta = {
        'abstract': True,
    }


class AnalysisJobGoTermAnnotation(BaseAnalysisJobAnnotation):

    go_term = mongoengine.LazyReferenceField(GoTerm, required=True)

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

    interpro_identifier = mongoengine.LazyReferenceField(
        InterproIdentifier,
        required=True
    )

    @property
    def accession(self):
        return self.interpro_identifier.accession

    @property
    def description(self):
        return self.interpro_identifier.description

    @property
    def lineage(self):
        return self.interpro_identifier.lineage


class AnalysisJobKeggModuleAnnotation(mongoengine.EmbeddedDocument):
    """KEGG modules on a given Analysis Job.
    """
    module = mongoengine.LazyReferenceField(KeggModule, required=True)
    completeness = mongoengine.FloatField(default=0.0)
    matching_kos = mongoengine.ListField(mongoengine.StringField(), default=list)
    missing_kos = mongoengine.ListField(mongoengine.StringField(), default=list)

    @property
    def accession(self):
        return self.module.accession

    @property
    def description(self):
        return self.module.description

    @property
    def name(self):
        return self.module.name


class AnalysisJobPfamAnnotation(BaseAnalysisJobAnnotation):
    """Pfam on a given Analysis Job.
    """
    pfam_entry = mongoengine.LazyReferenceField(PfamEntry, required=True)

    @property
    def accession(self):
        return self.pfam_entry.accession

    @property
    def description(self):
        return self.pfam_entry.description


class AnalysisJobCOGAnnotation(BaseAnalysisJobAnnotation):
    """COG on a given Analysis Job.
    """
    cog = mongoengine.LazyReferenceField(COG, required=True)

    @property
    def accession(self):
        return self.cog.accession

    @property
    def description(self):
        return self.cog.description


class AnalysisJobGenomePropAnnotation(mongoengine.EmbeddedDocument):
    """GenomeProperty on a given Analysis Job.
    """
    YES_PRESENCE = 1
    PARTIAL_PRESENCE = 2
    NO_PRESENCE = 3
    PRESENCE_CHOICES = (
        (YES_PRESENCE, 'Yes'),
        (PARTIAL_PRESENCE, 'Partial'),
        (NO_PRESENCE, 'No'),
    )
    genome_property = mongoengine.LazyReferenceField(GenomeProperty, required=True)
    presence = mongoengine.IntField(required=True, choices=PRESENCE_CHOICES)

    @property
    def accession(self):
        return self.genome_property.accession

    @property
    def description(self):
        return self.genome_property.description


class AnalysisJobKeggOrthologAnnotation(BaseAnalysisJobAnnotation):
    """KEGG KO on a given Analysis Job.
    """
    ko = mongoengine.LazyReferenceField(KeggOrtholog, required=True)

    @property
    def accession(self):
        return self.ko.accession

    @property
    def description(self):
        return self.ko.description


class AnalysisJobAntiSmashGCAnnotation(BaseAnalysisJobAnnotation):
    """antiSMASH gene cluster on a given Analysis Job
    """
    gene_cluster = mongoengine.LazyReferenceField(AntiSmashGeneCluster, required=True)

    @property
    def accession(self):
        return self.gene_cluster.accession

    @property
    def description(self):
        return self.gene_cluster.description


class BaseAnalysisJob(mongoengine.Document):

    analysis_id = mongoengine.StringField(primary_key=True, required=True)
    accession = mongoengine.StringField(required=True)
    pipeline_version = mongoengine.StringField(required=True)
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


class AnalysisJobKeggModule(BaseAnalysisJob):
    """KEGG module annotations.
    """
    kegg_modules = mongoengine.EmbeddedDocumentListField(
        AnalysisJobKeggModuleAnnotation, required=False)


class AnalysisJobPfam(BaseAnalysisJob):
    """Pfam entries for an analysis
    """
    pfam_entries = mongoengine.SortedListField(
        mongoengine.EmbeddedDocumentField(AnalysisJobPfamAnnotation),
        required=False, ordering='count', reverse=True)


class AnalysisJobKeggOrtholog(BaseAnalysisJob):
    """KeggOrtholog entries for an analysis
    """
    ko_entries = mongoengine.SortedListField(
        mongoengine.EmbeddedDocumentField(AnalysisJobKeggOrthologAnnotation),
        required=False, ordering='count', reverse=True)


class AnalysisJobGenomeProperty(BaseAnalysisJob):
    """Genome properties for an analysis
    """
    genome_properties = mongoengine.ListField(
        mongoengine.EmbeddedDocumentField(AnalysisJobGenomePropAnnotation), required=False)


class AnalysisJobAntiSmashGeneCluser(BaseAnalysisJob):
    """antiSMASH gene clusters for an analysis
    """
    antismash_gene_clusters = mongoengine.SortedListField(
        mongoengine.EmbeddedDocumentField(AnalysisJobAntiSmashGCAnnotation),
        required=False, ordering='count', reverse=True)

    meta = {
        'collection': 'analysis_job_antismash_gene_cluser'
    }


class Organism(mongoengine.Document):
    """Taxonomic model
    """
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
        'auto_create_index': False,
        'ordering': ['lineage'],
        'indexes': [
            'lineage',
        ]
    }


class AnalysisJobOrganism(mongoengine.EmbeddedDocument):

    count = mongoengine.IntField(required=True)
    organism = mongoengine.LazyReferenceField(Organism)

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

    class EMGMeta:
        pk_field = 'lineage'


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
    taxonomy_itsonedb = mongoengine.EmbeddedDocumentListField(
            AnalysisJobOrganism, required=False)
    taxonomy_itsunite = mongoengine.EmbeddedDocumentListField(
            AnalysisJobOrganism, required=False)


class AnalysisJobContig(mongoengine.Document):
    """An analysis job contig, this is used on assemblies
    """

    contig_id = mongoengine.StringField(required=True,
                                        unique_with=['accession', 'pipeline_version'])

    length = mongoengine.IntField()
    coverage = mongoengine.FloatField()

    analysis_id = mongoengine.StringField(required=True)
    accession = mongoengine.StringField(required=True)
    pipeline_version = mongoengine.StringField(required=True)
    job_id = mongoengine.IntField(required=True)

    cogs = mongoengine.EmbeddedDocumentListField(AnalysisJobCOGAnnotation, required=False)
    keggs = mongoengine.EmbeddedDocumentListField(AnalysisJobKeggOrthologAnnotation, required=False)
    gos = mongoengine.EmbeddedDocumentListField(AnalysisJobGoTermAnnotation, required=False)
    pfams = mongoengine.EmbeddedDocumentListField(AnalysisJobPfamAnnotation, required=False)
    interpros = mongoengine.EmbeddedDocumentListField(AnalysisJobInterproIdentifierAnnotation, required=False)
    as_geneclusters = mongoengine.EmbeddedDocumentListField(AnalysisJobAntiSmashGCAnnotation, required=False)
    kegg_modules = mongoengine.EmbeddedDocumentListField(AnalysisJobKeggModuleAnnotation, required=False)

    # Cache, using the _size_ method has an overhead
    has_cog = mongoengine.BooleanField(default=False)
    has_kegg = mongoengine.BooleanField(default=False)
    has_go = mongoengine.BooleanField(default=False)
    has_pfam = mongoengine.BooleanField(default=False)
    has_interpro = mongoengine.BooleanField(default=False)
    has_antismash = mongoengine.BooleanField(default=False)
    has_kegg_module = mongoengine.BooleanField(default=False)

    meta = {
        'auto_create_index': False,
        'indexes': [
            'contig_id',
            'analysis_id',
            'accession',
            'job_id',
            'pipeline_version',
            'length',  # ordering
            'coverage',  # ordering
            'cogs.cog',
            'keggs.ko',
            'gos.go_term',
            'pfams.pfam_entry',
            'interpros.interpro_identifier',
            'as_geneclusters.gene_cluster',
            'kegg_modules.module',
            'has_cog',
            'has_kegg',
            'has_go',
            'has_pfam',
            'has_interpro',
            'has_antismash',
            'has_kegg_module',
        ]
    }
