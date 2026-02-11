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

import os
import io

import logging
import urllib

import pysam

from django.conf import settings
from django.db.models import Q
from mongoengine.queryset.visitor import Q as M_Q

from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound

from mongoengine.base.datastructures import EmbeddedDocumentList
from rest_framework_mongoengine.viewsets import ReadOnlyModelViewSet as MongoReadOnlyModelViewSet

from emgapi import serializers as emg_serializers
from emgapi import models as emg_models
from emgapi import filters as emg_filters
from emgapi import utils as emg_utils
from emgapi.mixins import ExcessiveCSVException

from . import serializers as m_serializers
from . import models as m_models
from . import pagination as m_pagination
from . import viewsets as m_viewsets
from . import mixins as m_mixins
from .filters import MongoOrderingFilter

logger = logging.getLogger(__name__)


class GoTermViewSet(m_mixins.AnnotationRetrivalMixin, m_viewsets.ReadOnlyModelViewSet):
    """
    Provides list of GO terms.
    """
    annotation_model = m_models.GoTerm

    serializer_class = m_serializers.GoTermSerializer

    lookup_field = 'accession'
    lookup_value_regex = 'GO:[0-9]+'

    def get_serializer_class(self):
        return super(GoTermViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of GO terms
        Example:
        ---
        `/annotations/go-terms`
        """
        return super(GoTermViewSet, self) \
            .list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves GO term
        Example:
        ---
        `/annotations/go-terms/GO:009579`
        """
        return super(GoTermViewSet, self) \
            .retrieve(request, *args, **kwargs)


class InterproIdentifierViewSet(m_mixins.AnnotationRetrivalMixin, m_viewsets.ReadOnlyModelViewSet):
    """
    Provides list of InterPro identifiers.
    """
    annotation_model = m_models.InterproIdentifier

    serializer_class = m_serializers.InterproIdentifierSerializer

    lookup_field = 'accession'
    lookup_value_regex = 'IPR[0-9]+'

    def get_serializer_class(self):
        return super(InterproIdentifierViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of InterPro identifier
        Example:
        ---
        `/annotations/interpro-identifier`
        """
        return super(InterproIdentifierViewSet, self) \
            .list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves InterPro identifier
        Example:
        ---
        `/annotations/interpro-identifier/IPR020405`
        """
        return super(InterproIdentifierViewSet, self) \
            .retrieve(request, *args, **kwargs)


class KeggModuleViewSet(m_mixins.AnnotationRetrivalMixin, m_viewsets.ReadOnlyModelViewSet):
    """
    Provides list of KEEG modules.
    """
    annotation_model = m_models.KeggModule

    serializer_class = m_serializers.KeggModuleSerializer

    lookup_field = 'accession'
    lookup_value_regex = 'M[0-9]+'

    def get_serializer_class(self):
        return super(KeggModuleViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of KEGG modules
        Example:
        ---
        `/annotations/kegg-modules`
        """
        return super(KeggModuleViewSet, self) \
            .list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves KEGG module
        Example:
        ---
        `/annotations/kegg-modules/M00127`
        """
        return super(KeggModuleViewSet, self) \
            .retrieve(request, *args, **kwargs)


class PfamEntryViewSet(m_mixins.AnnotationRetrivalMixin, m_viewsets.ReadOnlyModelViewSet):
    """
    Provides list of Pfem entries.
    """
    annotation_model = m_models.PfamEntry

    serializer_class = m_serializers.PfamSerializer

    lookup_field = 'accession'
    lookup_value_regex = 'PF[0-9]+'

    def get_serializer_class(self):
        return super(PfamEntryViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of Pfam entries
        Example:
        ---
        `/annotations/pfam-entries`
        """
        return super(PfamEntryViewSet, self) \
            .list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves a Pfram entry
        Example:
        ---
        `/annotations/pfam-entry/P0001`
        """
        return super(PfamEntryViewSet, self) \
            .retrieve(request, *args, **kwargs)


class KeggOrthologViewSet(m_mixins.AnnotationRetrivalMixin, m_viewsets.ReadOnlyModelViewSet):
    """
    Provides list of KEGG Ortholog.
    """
    annotation_model = m_models.KeggOrtholog

    serializer_class = m_serializers.KeggOrthologSerializer

    lookup_field = 'accession'
    lookup_value_regex = 'K[0-9]+'

    def get_serializer_class(self):
        return super(KeggOrthologViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of KO
        Example:
        ---
        `/annotations/ko`
        """
        return super(KeggOrthologViewSet, self) \
            .list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves a Kegg Ortholog
        Example:
        ---
        `/annotations/ko/ko00001`
        """
        return super(KeggOrthologViewSet, self) \
            .retrieve(request, *args, **kwargs)


class GenomePropViewSet(m_mixins.AnnotationRetrivalMixin, m_viewsets.ReadOnlyModelViewSet):
    """
    Provides list of Genome Properties.
    """
    annotation_model = m_models.GenomeProperty

    serializer_class = m_serializers.GenomePropertySerializer

    lookup_field = 'accession'
    lookup_value_regex = 'GenProp[0-9]+'

    def get_serializer_class(self):
        return super(GenomePropViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of Genome properties
        Example:
        ---
        `/annotations/genome-properties`
        """
        return super(GenomePropViewSet, self) \
            .list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves a Genome property
        Example:
        ---
        `/annotations/genome-properties/GenProp0063`
        """
        return super(GenomePropViewSet, self) \
            .retrieve(request, *args, **kwargs)


class AntiSmashGeneClusterViewSet(m_mixins.AnnotationRetrivalMixin, m_viewsets.ReadOnlyModelViewSet):
    """Provides list of antiSMASH gene clusters.
    """
    annotation_model = m_models.AntiSmashGeneCluster

    serializer_class = m_serializers.AntiSmashGeneClusterSerializer

    lookup_field = 'accession'
    lookup_value_regex = '.*'

    def get_serializer_class(self):
        return super().get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of antiSMASH gene clusters
        Example:
        ---
        `/annotations/antismash-gene-clusters`
        """
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves an antiSMASH gene cluster
        Example:
        ---
        `/annotations/antismash-gene-clusters/terpene`
        """
        return super().retrieve(request, *args, **kwargs)


# FIXME: None of the RelationshipViewSet are working, on Master either...
class GoTermAnalysisRelationshipViewSet(m_viewsets.AnalysisRelationshipViewSet):
    """
    Retrieves list of analysis results for the given GO term
    Example:
    ---
    `/annotations/go-terms/GO:009579/analyses`
    """
    annotation_model = m_models.GoTerm

    def get_job_ids(self, annotation):
        job_ids = m_models.AnalysisJobGoTerm.objects \
            .filter(
                M_Q(go_slim__go_term=annotation) |
                M_Q(go_terms__go_term=annotation)
            ) \
            .distinct('job_id')
        return job_ids


class InterproIdentifierAnalysisRelationshipViewSet(m_viewsets.AnalysisRelationshipViewSet):
    """
    Retrieves list of analysis results for the given InterPro identifier
    Example:
    ---
    `/annotations/interpro-identifier/IPR020405/analyses`
    """
    annotation_model = m_models.InterproIdentifier

    def get_job_ids(self, annotation):
        return m_models.AnalysisJobInterproIdentifier.objects \
            .filter(M_Q(interpro_identifiers__interpro_identifier=annotation)) \
            .distinct('job_id')


class KeggModuleAnalysisRelationshipViewSet(m_viewsets.AnalysisRelationshipViewSet):
    """
    Retrieves list of analysis results for the given KEGG module M00127 term
    Example:
    ---
    `/annotations/kegg-modules/M00127/analyses`
    """
    annotation_model = m_models.KeggModule

    def get_job_ids(self, annotation):
        return m_models.AnalysisJobKeggModule.objects \
            .filter(M_Q(kegg_modules__module=annotation)) \
            .distinct('job_id')


class PfamAnalysisRelationshipViewSet(m_viewsets.AnalysisRelationshipViewSet):
    """
    Retrieves list of analysis results for the given Pfam entey P00001 term
    Example:
    ---
    `/annotations/pfram-entries/P00001/analyses`
    """

    annotation_model = m_models.AnalysisJobPfamAnnotation

    def get_job_ids(self, annotation):
        return m_models.AnalysisJobPfam.objects \
            .filter(M_Q(pfam_entries__pfam=annotation)) \
            .distinct('job_id')


class GenomePropertyAnalysisRelationshipViewSet(m_viewsets.AnalysisRelationshipViewSet):
    """
    Retrieves list of analysis results for the given antiSMASH gene cluster term
    Example:
    ---
    `/annotations/genome-properties/GenProp0017`
    """
    annotation_model = m_models.GenomeProperty

    def get_job_ids(self, annotation):
        return m_models.AnalysisJobGenomeProperty.objects \
            .filter(M_Q(genome_properties__genome_property=annotation)) \
            .distinct('job_id')


class AntiSmashGeneClusterAnalysisRelationshipViewSet(m_viewsets.AnalysisRelationshipViewSet):
    """Retrieves list of analysis results for the given Genome Property term
    Example:
    ---
    `/annotations/GenProp0063/analyses`
    """

    annotation_model = m_models.AntiSmashGeneCluster

    def get_job_ids(self, annotation):
        return m_models.AnalysisJobAntiSmashGeneCluser.objects \
            .filter(M_Q(antismash_gene_clusters__gene_cluster=annotation)) \
            .distinct('job_id')


class KeggOrthologRelationshipViewSet(m_viewsets.AnalysisRelationshipViewSet):
    """
    Retrieves list of analysis results for the given Kegg Ortholog
    Example:
    ---
    `/annotations/kos/ko00001/analyses`
    """

    annotation_model = m_models.KeggOrtholog

    def get_job_ids(self, annotation):
        return m_models.AnalysisJobKeggOrtholog.objects \
            .filter(M_Q(ko_entries__ko=annotation)) \
            .distinct('job_id')


class AnalysisGoTermRelationshipViewSet(m_mixins.AnalysisJobAnnotationMixin,
                                        m_viewsets.ListReadOnlyModelViewSet):
    """
    Retrieves GO terms for the given accession
    Example:
    ---
    `/analyses/MGYA00102827/go-terms`
    """
    serializer_class = m_serializers.GoTermRetriveSerializer

    pagination_class = m_pagination.MaxSetPagination

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobGoTerm

    annotation_model_property = 'go_terms'

    analysis_job_filters = ~Q(experiment_type__experiment_type='amplicon')


class AnalysisGoSlimRelationshipViewSet(m_mixins.AnalysisJobAnnotationMixin,
                                        m_viewsets.ListReadOnlyModelViewSet):
    """
    Retrieves GO slim for the given accession
    Example:
    ---
    `/analyses/MGYA00102827/go-slim`
    """
    serializer_class = m_serializers.GoTermRetriveSerializer

    pagination_class = m_pagination.MaxSetPagination

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobGoTerm

    annotation_model_property = 'go_slim'

    analysis_job_filters = ~Q(experiment_type__experiment_type='amplicon')


class AnalysisInterproIdentifierRelationshipViewSet(  # NOQA
    m_mixins.AnalysisJobAnnotationMixin,
    m_viewsets.ListReadOnlyModelViewSet):
    """
    Retrieves InterPro identifiers for the given accession
    Example:
    ---
    `/analyses/MGYA00102827/interpro-identifiers`
    """

    serializer_class = m_serializers.InterproIdentifierRetriveSerializer

    pagination_class = m_pagination.MaxSetPagination

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobInterproIdentifier

    annotation_model_property = 'interpro_identifiers'

    analysis_job_filters = ~Q(experiment_type__experiment_type='amplicon')


class AnalysisPfamRelationshipViewSet(  # NOQA
    m_mixins.AnalysisJobAnnotationMixin,
    m_viewsets.ListReadOnlyModelViewSet):
    """
    Retrieves Pfam entries for the given accession
    Example:
    ---
    `/analyses/MGYA00102827/pfam-entries`
    """

    serializer_class = m_serializers.PfamRetrieveSerializer

    pagination_class = m_pagination.MaxSetPagination

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobPfam

    annotation_model_property = 'pfam_entries'


class AnalysisKeggModulesRelationshipViewSet(  # NOQA
    m_mixins.AnalysisJobAnnotationMixin,
    m_viewsets.ListReadOnlyModelViewSet):
    """
    Retrieves KEGG Module for the given accession
    Example:
    ---
    `/analyses/MGYA00102827/kegg-modules`
    """

    serializer_class = m_serializers.KeggModuleRetrieveSerializer

    pagination_class = m_pagination.MaxSetPagination

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobKeggModule

    annotation_model_property = 'kegg_modules'


class AnalysisKeggOrthologsRelationshipViewSet(  # NOQA
    m_mixins.AnalysisJobAnnotationMixin,
    m_viewsets.ListReadOnlyModelViewSet):
    """
    Retrieves Kegg Orthologs for the given accession
    Example:
    ---
    /analyses/MGYA00102827/kegg-orthologs
    """

    serializer_class = m_serializers.KeggOrthologRetrieveSerializer

    pagination_class = m_pagination.MaxSetPagination

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobKeggOrtholog

    annotation_model_property = 'ko_entries'


class AnalysisGenomePropertiesRelationshipViewSet(  # NOQA
    m_mixins.AnalysisJobAnnotationMixin,
    m_viewsets.ListReadOnlyModelViewSet):
    """
    Retrieves GenomeProperties for the given accession
    Example:
    ---
    `/analyses/MGYA00102827/genome-properties`
    """

    serializer_class = m_serializers.GenomePropertyRetrieveSerializer

    pagination_class = m_pagination.MaxSetPagination

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobGenomeProperty

    annotation_model_property = 'genome_properties'


class AnalysisAntiSmashGeneClustersRelationshipViewSet(m_mixins.AnalysisJobAnnotationMixin,
                                                       m_viewsets.ListReadOnlyModelViewSet):
    """Retrieves the antiSMASH gene clusters for the given accession
    Example:
    ---
    `/analyses/MGYA00102827/antismash-gene-clusters`
    """

    serializer_class = m_serializers.AntiSmashGeneClusterRetrieveSerializer

    pagination_class = m_pagination.MaxSetPagination

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobAntiSmashGeneCluser

    annotation_model_property = 'antismash_gene_clusters'


class OrganismViewSet(m_viewsets.ListReadOnlyModelViewSet):

    """
    Provides list of Organisms.
    """

    serializer_class = m_serializers.OrganismSerializer

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'name',
        'lineage',
    )

    lookup_field = 'lineage'
    lookup_value_regex = '.*'

    def get_queryset(self):
        return m_models.Organism.objects.all()

    def get_serializer_class(self):
        return super(OrganismViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of Organisms
        Example:
        ---
        `/annotations/organisms`
        """
        return super(OrganismViewSet, self) \
            .list(request, *args, **kwargs)


class OrganismTreeViewSet(m_viewsets.ListReadOnlyModelViewSet):
    """
    Provides list of Organisms.
    """

    serializer_class = m_serializers.OrganismSerializer

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'name',
        'domain',
        'lineage',
    )

    lookup_field = 'lineage'
    lookup_value_regex = '[^/]+'

    def get_queryset(self):
        lineage = urllib.parse.unquote(
            self.kwargs.get('lineage', None).strip())
        organism = m_models.Organism.objects \
            .filter(lineage=lineage) \
            .only('name').distinct('name')
        if len(organism) == 0:
            raise Http404(("Attribute error '%s'." % self.lookup_field))
        queryset = m_models.Organism.objects \
            .filter(M_Q(ancestors__in=organism) | M_Q(name__in=organism))
        return queryset

    def get_serializer_class(self):
        return super(OrganismTreeViewSet, self).get_serializer_class()

    def get_serializer_context(self):
        context = super(OrganismTreeViewSet, self).get_serializer_context()
        context['lineage'] = self.kwargs.get('lineage')
        return context

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of Organisms
        Example:
        ---
        `/annotations/organisms/Bacteria:Chlorobi/children`
        """
        return super(OrganismTreeViewSet, self) \
            .list(request, *args, **kwargs)


class AnalysisOrganismRelationshipViewSet(m_mixins.AnalysisJobAnnotationMixin,
                                          m_viewsets.ListReadOnlyModelViewSet):
    """Retrieves Taxonomic analysis for the given accession
    Example:
    ---
    `/analyses/MGYA00102827/taxonomy`
    ---
    """
    serializer_class = m_serializers.OrganismRetriveSerializer

    pagination_class = m_pagination.MaxSetPagination

    filter_backends = (
        MongoOrderingFilter,
    )

    ordering_fields = (
        'name',
        'lineage',
    )

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobTaxonomy

    def annotation_model_property_resolver(self, analysis):
        """Get the taxonomic annotations using the following order:
        - SSU -> version <= 5.0 of pipeline
        - SSU >= 5.0 of pipeline
        - ITS OneDB {}
        - ITS unite
        - LSU
        """
        alternatives = [
            "taxonomy",
            "taxonomy_ssu",
            "taxonomy_itsonedb",
            "taxonomy_unite"
            "taxonomy_lsu",
        ]
 
        for alt in alternatives:
            try:
                return getattr(analysis, alt)
            except AttributeError:
                pass

        return EmbeddedDocumentList([], self.annotation_model, "taxonomy")


class AnalysisOrganismSSURelationshipViewSet(  # NOQA
    m_mixins.AnalysisJobAnnotationMixin,
    m_viewsets.ListReadOnlyModelViewSet):
    """Retrieves SSU Taxonomic analysis for the given accession
    Example:
    ---
    `/analyses/MGYA00102827/taxonomy/ssu`
    ---
    """
    serializer_class = m_serializers.OrganismRetriveSerializer

    pagination_class = m_pagination.MaxSetPagination

    filter_backends = (
        MongoOrderingFilter,
    )

    ordering_fields = (
        'name',
        'lineage',
    )

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobTaxonomy

    annotation_model_property = 'taxonomy_ssu'


class AnalysisOrganismLSURelationshipViewSet(  # NOQA
    m_mixins.AnalysisJobAnnotationMixin,
    m_viewsets.ListReadOnlyModelViewSet):
    """Retrieves LSU Taxonomic analysis for the given accession
    Example:
    ---
    `/analyses/MGYA00102827/taxonomy/lsu`
    ---
    """
    serializer_class = m_serializers.OrganismRetriveSerializer

    pagination_class = m_pagination.MaxSetPagination

    filter_backends = (
        MongoOrderingFilter,
    )

    ordering_fields = (
        'name',
        'lineage',
    )

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobTaxonomy

    annotation_model_property = 'taxonomy_lsu'


class AnalysisOrganismITSOneDBRelationshipViewSet(  # NOQA
    m_mixins.AnalysisJobAnnotationMixin,
    m_viewsets.ListReadOnlyModelViewSet):
    """Retrieves ITSoneDB Taxonomic analysis for the given accession
    Example:
    ---
    `/analyses/MGYA00102827/taxonomy/itsonedb`
    ---
    """
    serializer_class = m_serializers.OrganismRetriveSerializer

    pagination_class = m_pagination.MaxSetPagination

    filter_backends = (
        MongoOrderingFilter,
    )

    ordering_fields = (
        'name',
        'lineage',
    )

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobTaxonomy

    annotation_model_property = 'taxonomy_itsonedb'


class AnalysisOrganismITSUniteRelationshipViewSet(  # NOQA
    m_mixins.AnalysisJobAnnotationMixin,
    m_viewsets.ListReadOnlyModelViewSet):
    """Retrieves ITS UNITE Taxonomic analysis for the given accession
    Example:
    ---
    `/analyses/MGYA00102827/taxonomy/unite`
    ---
    """
    serializer_class = m_serializers.OrganismRetriveSerializer

    pagination_class = m_pagination.MaxSetPagination

    filter_backends = (
        MongoOrderingFilter,
    )

    ordering_fields = (
        'name',
        'lineage',
    )

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobTaxonomy

    annotation_model_property = 'taxonomy_itsunite'


class AnalysisTaxonomyOverview(APIView):
    """Get the counts for each taxonomic results for an analysis job.
    """

    def get(self, request, accession):
        """Get the AnalysisJob and then the AnalysisJobTaxonomy
        """
        job = get_object_or_404(
            emg_models.AnalysisJob,
            Q(pk=int(accession.lstrip('MGYA')))
        )
        analysis = None
        try:
            analysis = m_models.AnalysisJobTaxonomy.objects \
                .get(analysis_id=str(job.job_id))
        except m_models.AnalysisJobTaxonomy.DoesNotExist:
            raise Http404

        return Response({
            'accession': analysis.accession,
            'pipeline_version': analysis.pipeline_version,
            'taxonomy_count': len(getattr(analysis, 'taxonomy', [])),
            'taxonomy_ssu_count': len(getattr(analysis, 'taxonomy_ssu', [])),
            'taxonomy_lsu_count': len(getattr(analysis, 'taxonomy_lsu', [])),
            'taxonomy_itsunite_count': len(getattr(analysis, 'taxonomy_itsunite', [])),
            'taxonomy_itsonedb_count': len(getattr(analysis, 'taxonomy_itsonedb', []))
        })


class OrganismAnalysisRelationshipViewSet(m_viewsets.ListReadOnlyModelViewSet):

    serializer_class = emg_serializers.AnalysisSerializer

    filterset_class = emg_filters.AnalysisJobFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    ordering_fields = (
        'job_id',
    )

    ordering = ('-job_id',)

    search_fields = (
        '@sample__metadata__var_val_ucv',
    )

    lookup_field = 'lineage'

    def get_queryset(self):
        lineage = urllib.parse.unquote(
            self.kwargs.get(self.lookup_field, None).strip())
        organism = m_models.Organism.objects.filter(lineage=lineage) \
            .only('id')

        if len(organism) == 0:
            raise NotFound("Lineage not found. Lineage: " + lineage)

        job_ids = m_models.AnalysisJobTaxonomy.objects \
            .filter(
                M_Q(taxonomy__organism__in=organism) |
                M_Q(taxonomy_lsu__organism__in=organism) |
                M_Q(taxonomy_ssu__organism__in=organism)
            ).distinct('job_id')

        return emg_models.AnalysisJob.objects \
            .filter(job_id__in=job_ids) \
            .available(self.request)

    def get_serializer_class(self):
        return emg_serializers.AnalysisSerializer

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of analysis results for the given Organism
        Example:
        ---
        `/annotations/organisms/Bacteria:Chlorobi:OPB56/analysis`
        """

        return super(OrganismAnalysisRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class AnalysisContigViewSet(MongoReadOnlyModelViewSet):

    lookup_field = 'contig_id'
    lookup_value_regex = '[^/]+'

    ordering = ('id',)

    serializer_class = m_serializers.AnalysisJobContigSerializer
    pagination_class = m_pagination.CursorPagination
    pagination_class.ordering = ordering

    def get_object(self, ):
        try:
            pk = int(self.kwargs['accession'].lstrip('MGYA'))
        except ValueError:
            raise Http404()
        query_set = emg_models.AnalysisJob.objects.available(self.request)
        return get_object_or_404(query_set, Q(pk=pk))

    def get_queryset(self): # noqa C901
        """Filter the analysis job contigs
        """
        obj = self.get_object()

        queryset = m_models.AnalysisJobContig.objects
        request = self.request

        # Do not paginate CSV
        if request.accepted_renderer.format == 'csv':
            if queryset.count() > 50 * settings.EMG_DEFAULT_LIMIT:
                raise ExcessiveCSVException
            else:
                self.pagination_class = None

        query_filter = M_Q()

        # TODO: simplify!
        filter_cog = request.GET.get('cog', '').upper()
        if filter_cog:
            query_filter |= M_Q(cogs__cog=filter_cog)

        filter_kegg = request.GET.get('kegg', '').upper()
        if filter_kegg:
            query_filter |= M_Q(keggs__ko=filter_kegg)

        filter_go = request.GET.get('go', '').upper()
        if filter_go:
            query_filter |= M_Q(gos__go_term=filter_go)

        filter_interpro = request.GET.get('interpro', '').upper()
        if filter_interpro:
            query_filter |= M_Q(interpros__interpro_identifier=filter_interpro)

        filter_pfam = request.GET.get('pfam', '').upper()
        if filter_pfam:
            query_filter |= M_Q(pfams__pfam_entry=filter_pfam)

        filter_antismash = request.GET.get('antismash', '').lower()
        if filter_antismash:
            query_filter |= M_Q(as_geneclusters__gene_cluster=filter_antismash)

        if 'facet[]' in request.GET:
            facets = request.GET.getlist('facet[]')
            # TODO: try to simplify this
            facet_qs = M_Q()
            if len(facets):
                for facet in [f for f in facets if getattr(m_models.AnalysisJobContig, 'has_' + f, False)]:
                    facet_qs |= M_Q(**{'has_' + facet: True})
            else:
                # contigs with no annotations
                for f in m_models.AnalysisJobContig._fields:
                    if f.startswith('has_'):
                        facet_qs &= M_Q(**{f: False})
            query_filter &= (facet_qs)

        len_filter = M_Q()
        filter_gt = request.GET.get('gt', None)
        filter_lt = request.GET.get('lt', None)

        if filter_gt:
            len_filter &= M_Q(length__gte=filter_gt)
        if filter_lt:
            len_filter &= M_Q(length__lte=filter_lt)

        if len_filter:
            query_filter &= (len_filter)

        search = request.GET.get('search', '')
        if search:
            query_filter &= M_Q(contig_id__icontains=search)

        identifier = M_Q(job_id=obj.job_id, pipeline_version=obj.pipeline.release_version)

        return queryset.filter(identifier & query_filter)

    def retrieve(self, *args, **kwargs):
        """Retrieve a contig fasta file.
        The Fasta file will be retrieved using pysam.

        Example:
        ---
        `/analyses/<accession>/contigs/<contig_id>`
        ---
        """
        obj = self.get_object()
        contig = self.kwargs['contig_id']

        fasta_path = os.path.abspath(os.path.join(
            settings.RESULTS_DIR,
            obj.result_directory,
            obj.input_file_name + '.fasta.bgz')
        )
        fasta_idx_path = os.path.abspath(os.path.join(
            settings.RESULTS_DIR,
            obj.result_directory,
            obj.input_file_name + '.fasta.bgz.fai')
        )
        fasta_idx_gzi_path = os.path.abspath(os.path.join(
            settings.RESULTS_DIR,
            obj.result_directory,
            obj.input_file_name + '.fasta.bgz.gzi')
        )

        if os.path.isfile(fasta_path) and os.path.isfile(fasta_idx_path):
            output = io.StringIO()
            # TODO: handle errors
            with pysam.FastaFile(filename=fasta_path,
                                 filepath_index=fasta_idx_path,
                                 filepath_index_compressed=fasta_idx_gzi_path) as fasta:
                rows = fasta.fetch(contig)
                output.write('>' + emg_utils.assembly_contig_name(contig) + '\n')
                for row in rows:
                    output.write(row)
            response = HttpResponse()
            response['Content-Type'] = 'text/x-fasta'
            response['Content-Disposition'] = 'attachment; filename={0}.fasta'.format(contig)
            output.seek(0, os.SEEK_END)
            response['Content-Length'] = output.tell()
            response.write(output.getvalue())
            return response

        if settings.DEBUG:
            return Response('Contig {0} not found.'.format(fasta_path), status.HTTP_404_NOT_FOUND)
        else:
            return Response('Contig not found.', status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], url_path='annotations')
    def retrieve_gff(self, request, *args, **kwargs):
        """Retrieve a contig GFF file.
        The are 2 flavors for the GFF files:
        - COG,KEGG, Pfam, InterPro and EggNOG annotations
        - antiSMASH
        By default the action will return the 'main one', unless specified using the querystring param 'antismash=True'
        The GFF file will be parsed with pysam and sliced.
        Example:
        ---
        /analyses/<accession>/<contig_id>/annotation
        ---
        """
        obj = self.get_object()
        contig = self.kwargs['contig_id']

        file_prefix = 'annotations'
        folder = 'functional-annotation'

        if self.request.GET.get('antismash', False):
            file_prefix = 'antismash'
            folder = 'pathways-systems'

        gff_path = os.path.abspath(os.path.join(
            settings.RESULTS_DIR,
            obj.result_directory,
            folder,
            '{}.{}.gff.bgz'.format(obj.input_file_name, file_prefix))
        )
        gff_idx_path = os.path.abspath(os.path.join(
            settings.RESULTS_DIR,
            obj.result_directory,
            folder,
            '{}.{}.gff.bgz.tbi'.format(obj.input_file_name, file_prefix))
        )

        if os.path.isfile(gff_path) and os.path.isfile(gff_idx_path):
            # multiple_iterators = True as many processes
            # could be using the same file at the same moment
            output = io.StringIO()
            try:
                with pysam.TabixFile(filename=gff_path, index=gff_idx_path) as gff:
                    rows = gff.fetch(contig, multiple_iterators=True)
                    for row in rows:
                        output.write(emg_utils.assembly_contig_name(row) + '\n')
                response = HttpResponse()
                response['Content-Type'] = 'text/x-gff3'
                response['Content-Disposition'] = 'attachment; filename={0}.gff'.format(contig)
                output.seek(0, os.SEEK_END)
                response['Content-Length'] = output.tell()
                response.write(output.getvalue())
                return response
            except ValueError:
                return Response('Contig not found on GFF file.', status.HTTP_404_NOT_FOUND)

        if settings.DEBUG:
            return Response('No GFF file for contig {0}.'.format(contig), status.HTTP_404_NOT_FOUND)
        else:
            return Response('No GFF file for contig.', status.HTTP_404_NOT_FOUND)
